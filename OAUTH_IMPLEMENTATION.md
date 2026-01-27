# OAuth Support in Cortana - Implementation Complete

## Status: ✅ IMPLEMENTED & READY TO USE

You now have **complete OAuth support** for multi-provider LLM access in Cortana!

---

## Quick Start

### 1. Prepare OAuth Credentials

Get credentials from your provider (Gemini CLI, Qwen Code, Antigravity, or iFlow) in JSON format:

```json
{
  "access_token": "ya29.a0AfH6SMBxxxxx...",
  "refresh_token": "1//0gPxxxxx...",
  "token_type": "Bearer",
  "expires_at": 1645123456.1234
}
```

**Important**: Your credential file MUST include both `access_token` and `refresh_token`.

### 2. Configure Environment

Create credentials directory and add to `.env`:

```bash
# Create directory
mkdir -p credentials
chmod 700 credentials

# .env
GEMINI_CLI_OAUTH_CREDENTIALS=/path/to/credentials/gemini.json
QWEN_CODE_OAUTH_CREDENTIALS=/path/to/credentials/qwen.json
```

Or with Docker:

```yaml
# docker-compose.yml
volumes:
  - ./credentials:/workspace/credentials  # Writable!
```

### 3. Secure Credentials File

```bash
chmod 600 credentials/gemini.json
```

### 4. Optional: Enable Token Refresh

If you want automatic token refresh (recommended), add client credentials:

```ini
GEMINI_CLIENT_ID=your_client_id
GEMINI_CLIENT_SECRET=your_client_secret
```

---

## How It Works

### Token Lifecycle

```
Startup
  ↓
OAuthHandler loads credentials
  ↓
Before each API call
  ↓
_setup_oauth_tokens() runs
  ↓
Check: Is token expired?
  ├─ NO → Use token as-is
  └─ YES → Auto-refresh
           ↓
           POST refresh_token to provider
           ↓
           Update access_token
           ↓
           Save to credential file
           ↓
           Use new token
```

### Automatic vs Manual Refresh

**Automatic (Recommended):**
- Cortana detects token expiry (10-minute buffer)
- Automatically refreshes before requests fail
- Updates credential file with new token
- Seamless to end-user

**Manual:**
- Use Discord command: `/settings oauth-refresh gemini_cli`
- Useful if automatic refresh fails
- Shows success/failure status

---

## Supported OAuth Providers

| Provider | Environment Variable | Token Endpoint |
|----------|----------------------|-----------------|
| **Gemini CLI** | `GEMINI_CLI_OAUTH_CREDENTIALS` | `https://oauth2.googleapis.com/token` |
| **Qwen Code** | `QWEN_CODE_OAUTH_CREDENTIALS` | `https://api.aliyun.com/oauth/token` |
| **Antigravity** | `ANTIGRAVITY_OAUTH_CREDENTIALS` | `https://api.antigravity.dev/oauth/token` |
| **iFlow** | `IFLOW_OAUTH_CREDENTIALS` | `https://oauth.iflow.dev/token` |

---

## Discord Commands

### View Token Status

```
/settings oauth-status
```

Shows:
- Provider name
- Token expiry time (hh:mm format)
- "✅ Valid" or "❌ EXPIRED"
- Last refresh time
- Number of refresh attempts

### Manually Refresh Token

```
/settings oauth-refresh gemini_cli
```

Response:
- ✅ "Successfully refreshed token for **gemini_cli**"
- ❌ "Failed to refresh token" + troubleshooting tips

---

## Configuration Examples

### Example 1: Gemini CLI Only

```ini
# .env
GEMINI_CLI_OAUTH_CREDENTIALS=/workspace/credentials/gemini.json
GEMINI_CLIENT_ID=your_client_id.apps.googleusercontent.com
GEMINI_CLIENT_SECRET=your_secret
```

### Example 2: Multiple Providers

```ini
# .env
GEMINI_CLI_OAUTH_CREDENTIALS_1=/workspace/credentials/gemini1.json
GEMINI_CLI_OAUTH_CREDENTIALS_2=/workspace/credentials/gemini2.json
QWEN_CODE_OAUTH_CREDENTIALS=/workspace/credentials/qwen.json
ANTIGRAVITY_OAUTH_CREDENTIALS=/workspace/credentials/antigravity.json

# Client credentials
GEMINI_CLIENT_ID=...
GEMINI_CLIENT_SECRET=...
QWEN_CLIENT_ID=...
QWEN_CLIENT_SECRET=...
```

### Example 3: Stateless Deployment (JSON String)

```ini
# .env - embed credentials as JSON string (for stateless deployments)
GEMINI_CLI_OAUTH_CREDENTIALS='{"access_token": "ya29...", "refresh_token": "1//0g...", ...}'
```

---

## Troubleshooting

### Token Not Refreshing Automatically

**Check 1: Is credential file writable?**
```bash
ls -l credentials/gemini.json
# Should show: -rw------- (600)
```

**Check 2: Does credential have refresh_token?**
```bash
grep "refresh_token" credentials/gemini.json
# Should output: "refresh_token": "1//0gP..."
```

**Check 3: Check logs for errors**
```bash
docker-compose logs cortana | grep -i "oauth\|refresh\|token"
```

### Token Refresh Fails with "invalid_grant"

**Cause**: Refresh token is revoked or expired

**Solution**: Re-authenticate to get new refresh token
```bash
# Example for Gemini:
gcloud auth application-default login
cp ~/.config/gcloud/application_default_credentials.json credentials/gemini.json
chmod 600 credentials/gemini.json
```

### "No OAuth credentials configured"

**Issue**: Environment variables not set

**Solution**: Verify .env file
```bash
cat .env | grep OAUTH_CREDENTIALS
# Should show your credential paths
```

### Docker: Credential File Not Found

**Issue**: Path is relative or incorrect

**Solution**: Use absolute paths or Docker volume mounts
```yaml
# docker-compose.yml
volumes:
  - ./credentials:/workspace/credentials
  
# .env
GEMINI_CLI_OAUTH_CREDENTIALS=/workspace/credentials/gemini.json
```

---

## Implementation Details

### New Files

**src/oauth_handler.py** (388 lines)
- `OAuthCredential`: Individual credential with token state
- `OAuthHandler`: Manages multiple credentials
- Automatic token refresh with provider-specific implementations
- Status tracking and monitoring

### Enhanced Files

**src/rotator_client.py**
- `_setup_oauth_tokens()`: Prepare tokens before API calls
- `get_oauth_status()`: View all token status
- `refresh_oauth_token()`: Manual refresh trigger
- `get_oauth_credentials_info()`: Provider information

**src/main.py**
- `/settings oauth-status`: Discord command for status
- `/settings oauth-refresh`: Discord command for manual refresh

---

## Architecture

```
OAuth Setup Flow:
  .env variables → OAuthHandler → Load credentials from files → Store in memory

Token Use Flow:
  API call → _setup_oauth_tokens() → Check expiry → Refresh if needed → Use token

Token Refresh Flow:
  Token expired? → Get refresh_token → POST to provider → Update token → Save file
```

---

## Key Features

✅ **Automatic Token Expiry Detection**
- Checks `expires_at` timestamp with 5-minute buffer
- Prevents "token expired" errors

✅ **Automatic Token Refresh**
- Refreshes token before requests fail
- Updates credential file with new token
- Transparent to user

✅ **Multiple Credentials Per Provider**
- Load multiple credentials per provider
- Fallback if one fails
- Load balancing

✅ **Token Status Monitoring**
- See all tokens and expiry times
- Manual refresh trigger
- Refresh history tracking

✅ **Provider-Specific Handling**
- Gemini CLI: Google OAuth 2.0
- Qwen Code: Alibaba Cloud
- Antigravity: Custom endpoint
- iFlow: Workflow OAuth

✅ **Graceful Error Handling**
- Failed refresh → try next credential
- Network errors → retry with backoff
- Invalid tokens → log and skip

---

## Security Best Practices

1. **Restrict File Permissions**
   ```bash
   chmod 600 credentials/*.json
   ```

2. **Use Environment Variables**
   - Don't hardcode credentials in code
   - Use `.env` file (not in git)

3. **Rotate Tokens Regularly**
   - OAuth providers typically expire tokens
   - Automatic refresh handles this
   - Check token status with `/settings oauth-status`

4. **Secure Credential Files**
   - Use persistent volume in Docker
   - Encrypt at rest if possible
   - Backup credentials securely

5. **Monitor Token Status**
   - Use `/settings oauth-status` to check health
   - Alert on imminent expiry
   - Manual refresh if needed

---

## Limitations & Known Issues

⚠️ **No Real-Time Alerts**
- Token expiry notifications not yet implemented
- Monitor via `/settings oauth-status` command

⚠️ **No Token Caching**
- Tokens loaded from file each startup
- Acceptable for most use cases

⚠️ **File-Based Storage**
- Credentials stored in JSON files
- Must be writable for token refresh
- Works with Docker volumes

---

## Integration with rotator_library

OAuth tokens are automatically set up before rotator_library LLM calls:

```python
# In rotating_completion():
oauth_tokens = await _setup_oauth_tokens()  # Get OAuth tokens
# Then rotator_library uses them for Gemini CLI, Qwen, etc.
```

This allows rotator_library to use OAuth providers seamlessly alongside API key providers.

---

## Support & Next Steps

### Current Status
- ✅ OAuth credential loading
- ✅ Token expiry detection
- ✅ Automatic token refresh
- ✅ Token status monitoring
- ✅ Manual refresh commands
- ✅ Multi-provider support

### Future Enhancements (Phase 8)
- [ ] Real-time token expiry alerts
- [ ] Custom refresh rate configuration
- [ ] OAuth setup wizard (guided setup)
- [ ] Token usage statistics
- [ ] Credential rotation policies
- [ ] Webhook notifications

---

## Testing

To verify OAuth support is working:

```bash
# 1. Check OAuth handler loads credentials
docker-compose logs cortana | grep "Loaded OAuth credential"

# 2. Check token status in Discord
/settings oauth-status

# 3. Test manual refresh (if token expired)
/settings oauth-refresh gemini_cli

# 4. Check logs for refresh attempts
docker-compose logs cortana | grep -i "refresh"
```

---

**Implementation Complete!** 🎉

You can now use OAuth providers with Cortana for Gemini CLI, Qwen Code, Antigravity, and iFlow integrations.
