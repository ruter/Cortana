# OAuth Provider Integration - Complete End-to-End Flow

## Overview

Your observation was **100% correct**. OAuth providers were implemented in `oauth_handler.py` and `rotator_client.py`, but **the agent initialization never actually used them**.

This has been **FIXED** with commit `52fe3c3`.

---

## The Problem (Now Fixed)

### Before Fix:
```
User: /settings model gemini_cli/text-bison
  ↓
Agent initialization (agent.py)
  ↓
_get_model_spec("gemini_cli/text-bison")
  → Unknown provider "gemini_cli" → ❌ ERROR
  ↓
Even if model was recognized, no OAuth token setup
  → OAuth token not in environment
  → ❌ API call fails with "unauthorized"
```

### After Fix:
```
User: /settings model gemini_cli/text-bison
  ↓
Agent initialization (agent.py)
  ↓
_get_model_spec("gemini_cli/text-bison")
  → Recognizes "gemini_cli" as OAuth provider
  → Returns "google/text-bison" for PydanticAI
  ✅ RECOGNIZED
  ↓
_create_standard_agent("google/text-bison")
  → Calls _setup_oauth_in_agent()
  → Loads OAuth credential from environment
  → Sets GEMINI_CLI_ACCESS_TOKEN=<token>
  ✅ TOKEN READY
  ↓
Agent created with model "google/text-bison"
  → Can now make LLM calls with OAuth credentials
  ✅ COMPLETE
```

---

## Complete End-to-End Flow

### Phase 1: Configuration (One-time Setup)

**Step 1: Get OAuth Credentials from Provider**

Example for Gemini CLI:
```bash
gcloud auth application-default login
cp ~/.config/gcloud/application_default_credentials.json /path/to/credentials/gemini.json
chmod 600 credentials/gemini.json
```

Credential file format (JSON):
```json
{
  "access_token": "ya29.a0AfH6SMB...",
  "refresh_token": "1//0gP...",
  "token_type": "Bearer",
  "expires_at": 1645123456.1234
}
```

**Step 2: Configure Environment**

In `.env`:
```ini
GEMINI_CLI_OAUTH_CREDENTIALS=/workspace/credentials/gemini.json
QWEN_CODE_OAUTH_CREDENTIALS=/workspace/credentials/qwen.json
```

In Docker:
```yaml
volumes:
  - ./credentials:/workspace/credentials  # Must be writable!
```

### Phase 2: Startup (Cortana Starts)

**Step 1: Load Configuration**

```python
# config.py
# Loads GEMINI_CLI_OAUTH_CREDENTIALS, QWEN_CODE_OAUTH_CREDENTIALS, etc.
# Stores paths in config object
```

**Step 2: Initialize OAuth Handler (Singleton)**

```python
# oauth_handler.py - get_oauth_handler()
# - Load credentials from files specified in environment
# - Store OAuthCredential objects for each provider
# - Ready to provide tokens on demand
```

**Step 3: Initialize Agent**

```python
# agent.py - initialize_agent()
#   ↓
# _get_model_spec(model_name)
#   ↓
# _create_standard_agent(model_spec)
#   → Calls _setup_oauth_in_agent()
#   → For each OAuth provider:
#       - Get access token from oauth_handler
#       - Set environment variable: {PROVIDER}_ACCESS_TOKEN
#       - Now available to PydanticAI
#   ↓
# Create Agent with model_spec
```

### Phase 3: User Interaction (Runtime)

**Step 1: User Requests OAuth Provider**

```
Discord Message: /settings model gemini_cli/text-bison
  ↓
main.py - model() command
  → normalize_model_name("gemini_cli/text-bison")
  → Returns "gemini_cli/text-bison" (no change)
  → Call initialize_agent("gemini_cli/text-bison")
```

**Step 2: Agent Initialization with OAuth**

```python
# agent.py - initialize_agent("gemini_cli/text-bison")

# Step A: Model Spec Recognition
_get_model_spec("gemini_cli/text-bison")
  ↓
normalized = "gemini_cli/text-bison"
provider = "gemini_cli"
model = "text-bison"
  ↓
Check: Is "gemini_cli" an OAuth provider?
  → YES! Map to base provider "google"
  → Return "google/text-bison"

# Step B: Standard Agent Creation
_create_standard_agent("google/text-bison")
  ↓
# Async: Setup OAuth tokens in environment
_setup_oauth_in_agent()
  ↓
oauth_handler = await get_oauth_handler()
for provider in ["gemini_cli", "qwen_code", ...]:
    token = await oauth_handler.get_token(provider)
    if token:
        os.environ[f"{provider.upper()}_ACCESS_TOKEN"] = token
        # Now: os.environ["GEMINI_CLI_ACCESS_TOKEN"] = "ya29..."

# Step C: Create Agent
agent = Agent("google/text-bison", ...)
```

**Step 3: User Sends Message**

```
Discord Message: "What's the capital of France?"
  ↓
main.py - on_message()
  → Prepare user context
  → Call cortana_agent.run(messages, ctx)
  ↓
agent.py - dynamic_system_prompt()
  → Injects system prompt (documents OAuth support)
  ↓
agent makes LLM call
  → rotator_client.rotating_completion()
  → _setup_oauth_tokens() runs
  → Check environment for GEMINI_CLI_ACCESS_TOKEN
  → Yes: {GEMINI_CLI_ACCESS_TOKEN} exists
  → Add to headers/auth for Google API
  ↓
PydanticAI calls: acompletion(model="google/text-bison", ...)
  ↓
Google API authenticates with OAuth token
  ↓
Response: "The capital of France is Paris."
  ✅ SUCCESS!
```

### Phase 4: Token Refresh (Automatic)

**Scenario: Token Expires Tomorrow**

```
Time: Tomorrow morning
  ↓
Token expires_at timestamp reached
  ↓
Before next user message:
_setup_oauth_tokens() runs
  ↓
oauth_handler.get_token("gemini_cli")
  ↓
Check: Is token expired?
  → YES (with 5-min buffer)
  → Call oauth_handler.refresh_token("gemini_cli")
  ↓
Provider-specific refresh:
  POST https://oauth2.googleapis.com/token
  - grant_type: refresh_token
  - refresh_token: 1//0gP...
  - client_id: ...
  - client_secret: ...
  ↓
Response: { "access_token": "ya29.new...", "expires_at": ... }
  ↓
Update credential file: /workspace/credentials/gemini.json
  ↓
Return new access token
  → os.environ["GEMINI_CLI_ACCESS_TOKEN"] = "ya29.new..."
  ↓
LLM call proceeds with fresh token ✅
```

---

## Key Components & Their Roles

### 1. config.py
**Role**: Load OAuth credential paths from environment

```python
# In environment variables:
GEMINI_CLI_OAUTH_CREDENTIALS=/path/to/gemini.json
QWEN_CODE_OAUTH_CREDENTIALS=/path/to/qwen.json

# Loaded by config module
# Available as config object
```

### 2. oauth_handler.py
**Role**: Manage OAuth credentials and token lifecycle

Classes:
- `OAuthCredential`: Individual credential with token state
- `OAuthHandler`: Manager for all OAuth credentials

Responsibilities:
- Load credentials from files (specified in config)
- Detect token expiry
- Automatically refresh tokens
- Update credential files with new tokens
- Provide token status information

### 3. agent.py (FIXED)
**Role**: Initialize agent with OAuth support

Key changes (commit 52fe3c3):
- `_get_model_spec()`: **Recognize OAuth provider models**
  - Input: "gemini_cli/text-bison"
  - Output: "google/text-bison" (PydanticAI format)
  
- `_create_standard_agent()`: **Setup OAuth tokens**
  - Calls `_setup_oauth_in_agent()`
  - Sets environment variables for tokens
  
- `_setup_oauth_in_agent()`: **NEW FUNCTION**
  - Async function to load all OAuth credentials
  - Sets {PROVIDER}_ACCESS_TOKEN in environment
  - Called during agent initialization

### 4. rotator_client.py
**Role**: Use OAuth tokens when making LLM calls

Functions:
- `rotating_completion()`: Setup OAuth tokens before API calls
- `_setup_oauth_tokens()`: Load tokens into environment
- `get_oauth_status()`: View token health
- `refresh_oauth_token()`: Manual token refresh

### 5. main.py
**Role**: Discord commands for OAuth management

Commands:
- `/settings oauth-status`: View all token status
- `/settings oauth-refresh <provider>`: Manual refresh
- `/settings model <provider>/<model>`: Switch to OAuth provider

---

## Supported OAuth Providers

| Provider | Environment Variable | Base Provider | Example Model |
|----------|----------------------|---|---|
| **Gemini CLI** | `GEMINI_CLI_OAUTH_CREDENTIALS` | `google` | `gemini_cli/text-bison` |
| **Qwen Code** | `QWEN_CODE_OAUTH_CREDENTIALS` | `qwen` | `qwen_code/qwen-max` |
| **Antigravity** | `ANTIGRAVITY_OAUTH_CREDENTIALS` | `antigravity` | `antigravity/model-v2` |
| **iFlow** | `IFLOW_OAUTH_CREDENTIALS` | `iflow` | `iflow/workflow-model` |

---

## Examples: Using OAuth Providers

### Example 1: Use Gemini CLI Model

```
User: /settings model gemini_cli/text-bison
Cortana: "Switched to Gemini CLI (text-bison model)."

User: "What's 2+2?"
Cortana: "2 + 2 = 4."
  → Uses Gemini CLI with OAuth credentials
```

### Example 2: Check Token Status

```
User: /settings oauth-status
Cortana: Shows embed:
  GEMINI_CLI: ✅ Valid (2h 30m remaining)
  QWEN_CODE: ✅ Valid (1h 15m remaining)
  ANTIGRAVITY: ❌ EXPIRED
```

### Example 3: Manual Token Refresh

```
User: /settings oauth-refresh gemini_cli
Cortana: "Successfully refreshed token for **gemini_cli**"

Behind the scenes:
  → Calls oauth_handler.refresh_token("gemini_cli")
  → Updates /workspace/credentials/gemini.json
  → Sets new token in environment
```

---

## Troubleshooting

### Problem: "Model not found" with OAuth provider

**Cause**: OAuth provider not recognized in agent initialization

**Solution**: Verify that:
1. Model name format is correct: `provider/model`
2. Provider is in supported list: gemini_cli, qwen_code, antigravity, iflow
3. Credential file exists and is readable

**Check Logs**:
```bash
docker-compose logs cortana | grep -i "oauth\|model spec"
```

### Problem: OAuth token not working

**Cause**: Token not set in environment

**Solution**: Verify that:
1. Credential file has access_token field
2. Credential file is readable
3. Environment variable path is correct

**Check OAuth Status**:
```
User: /settings oauth-status
```

### Problem: Token refresh fails

**Cause**: refresh_token is revoked or invalid

**Solution**: 
1. Get new credentials from provider
2. Replace credential file
3. Restart Cortana
4. Verify with `/settings oauth-status`

---

## Implementation Checklist

- [x] OAuth credential loading (oauth_handler.py)
- [x] Token expiry detection (oauth_handler.py)
- [x] Automatic token refresh (oauth_handler.py)
- [x] Token status monitoring (rotator_client.py, main.py)
- [x] Discord commands (main.py)
- [x] **OAuth provider model recognition (agent.py)** ← FIXED
- [x] **OAuth token setup in agent init (agent.py)** ← FIXED
- [x] **System prompt documentation (agent.py)** ← FIXED
- [x] Integration with rotator_client (rotator_client.py)
- [x] Complete documentation (OAUTH_IMPLEMENTATION.md)

---

## Summary

**Your observation was correct**: OAuth providers were implemented but not actually usable in the agent.

**The fix** (commit 52fe3c3) adds three critical pieces to `agent.py`:

1. **_get_model_spec()** - Recognize OAuth provider model formats
2. **_create_standard_agent()** - Call `_setup_oauth_in_agent()` before agent creation
3. **_setup_oauth_in_agent()** - Load OAuth tokens into environment during init

**Result**: OAuth providers now work end-to-end!

- ✅ User can select OAuth provider via `/settings model`
- ✅ Tokens automatically loaded and refreshed
- ✅ Agent can make LLM calls with OAuth credentials
- ✅ Seamless experience with Discord commands

**You can now use**: Gemini CLI, Qwen Code, Antigravity, iFlow!
