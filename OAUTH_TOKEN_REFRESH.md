# OAuth Token Refresh in Cortana

## Quick Answer

**Will OAuth tokens refresh automatically?**

> **YES, likely** - but rotator_library handles it, not Cortana. The behavior depends on:
> 1. Credentials file must be **writable** (rotator updates it with new tokens)
> 2. Credentials must contain **refresh tokens** (not just access tokens)
> 3. Provider's token endpoint must be **accessible**
> 4. Refresh token itself must be **valid** (not revoked/expired)

---

## Current Implementation

### Token Lifecycle in Cortana

```
.env: GEMINI_CLI_OAUTH_CREDENTIALS=/path/to/creds.json
         ↓
config.py: Load credential file paths
         ↓
rotator_client.py: Pass to RotatingClient(oauth_credentials=...)
         ↓
rotator_library: Manage token refresh (AUTOMATIC)
         ↓
credentials/gemini.json: Update with new access token
```

### What Cortana Does

1. **Loads** OAuth credential file paths from environment variables
2. **Passes** them to rotator_library's RotatingClient
3. **Delegates** all token management to rotator_library
4. **Does NOT** explicitly manage or monitor token refresh

### What rotator_library Does (Expected)

According to OAuth 2.0 standard and rotator_library documentation:

✅ Detects token expiry (checks `expires_at` or `expires_in`)
✅ Automatically refreshes before/during requests
✅ Calls provider's token endpoint with `refresh_token`
✅ Updates credentials file with new `access_token` and `expires_at`
✅ Falls back to next credential if refresh fails
✅ Caches tokens to minimize refresh calls

---

## Requirements for Auto-Refresh to Work

### 1. Credentials File Must Be Writable

**Problem**: If the credentials file is read-only, rotator can't update it.

**Solution**:
```bash
# Ensure write permissions
chmod 600 /path/to/credentials/gemini.json
```

**Docker deployment**:
```yaml
# docker-compose.yml
volumes:
  - ./credentials:/workspace/credentials  # Writable volume
```

### 2. Credentials Must Contain Refresh Token

**Problem**: Some OAuth flows only return access tokens. If there's no refresh token, refresh is impossible.

**Check your credentials file**:
```json
{
  "access_token": "ya29.a0AfH6SMB...",    // ✅ Required
  "refresh_token": "1//0gP...",           // ✅ REQUIRED for auto-refresh
  "token_type": "Bearer",                  // ✅ Usually "Bearer"
  "expires_in": 3600,                      // ✅ Token lifetime in seconds
  "expires_at": 1645123456.1234            // ✅ Unix timestamp when it expires (optional)
}
```

**Missing refresh_token?** You'll need to re-authenticate (manual OAuth flow).

### 3. Provider's Token Endpoint Must Be Accessible

**Problem**: Network connectivity issues prevent token refresh.

**Solutions**:
- Ensure container has internet access
- Check firewall rules (if self-hosted)
- Verify proxy configuration if behind proxy

### 4. Refresh Token Must Not Be Revoked

**Problem**: Refresh tokens can be revoked by the user or provider.

**Signs**:
- Requests fail with "invalid_grant" error
- Token refresh stops working after weeks/months

**Solution**: Re-authenticate to get new refresh token.

---

## What Happens If Token Refresh Fails

### Scenario 1: Single Credential, Refresh Fails
```
Request → Token expired → Refresh fails → Request FAILS
         ↓
         User sees error
         Bot logs "invalid_grant" or similar
```

**No automatic fallback** (no other credential to try)

### Scenario 2: Multiple Credentials, First Refresh Fails
```
Request → Credential 1 expired → Refresh fails → Try Credential 2
         ↓ (if Credential 2 valid)
         Request succeeds
```

**Rotator automatically tries next credential**

### Scenario 3: All Credentials Expired & Can't Refresh
```
Request → All credentials expired → All refresh fail → Request FAILS
         ↓
         User sees error
         No automatic recovery
```

---

## Known Limitations (Not Implemented)

### 1. Token Refresh Monitoring
❌ No alerting if refreshes fail repeatedly
❌ No Discord notifications on token expiry
❌ No metrics on refresh success rate

### 2. Explicit Token Management
❌ No `/settings token-status` command
❌ No manual refresh trigger
❌ No credential reloading without restart

### 3. Error Handling
❌ No specific OAuth error messages to user
❌ No distinction between auth vs network errors

### 4. Logging
❌ Token refresh events not logged separately
❌ Credential loading not logged with timestamps

---

## Best Practice Setup

### 1. Credential Structure

Create credentials directory with secure permissions:
```bash
mkdir -p credentials
chmod 700 credentials
```

### 2. Configuration

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  cortana:
    volumes:
      - ./workspace:/workspace
      - ./credentials:/workspace/credentials  # Writable!
```

**.env**:
```ini
# Use full paths to mounted credentials
GEMINI_CLI_OAUTH_CREDENTIALS=/workspace/credentials/gemini.json
QWEN_CODE_OAUTH_CREDENTIALS=/workspace/credentials/qwen.json
```

### 3. Credentials File

**credentials/gemini.json**:
```json
{
  "type": "authorized_user",
  "client_id": "...",
  "client_secret": "...",
  "refresh_token": "1//0gP...",           // Essential!
  "access_token": "ya29.a0AfH6SMB...",
  "expires_at": 1645123456.1234,
  "expires_in": 3600
}
```

**Secure it**:
```bash
chmod 600 credentials/gemini.json
```

### 4. Testing Token Refresh

Monitor logs for token refresh:
```bash
# Docker logs
docker-compose logs -f cortana | grep -i "token\|refresh"

# Check if credentials file gets updated
watch -n 1 'ls -l credentials/gemini.json && head -20 credentials/gemini.json'
```

---

## Phase 8 Enhancement: Token Monitoring

To add explicit token refresh monitoring, consider:

### 1. Create refresh_monitor.py
```python
async def monitor_token_expiry():
    """Periodically check OAuth token expiry times."""
    while True:
        for provider, cred_paths in config.ROTATOR_OAUTH_CREDENTIALS.items():
            for path in cred_paths:
                try:
                    creds = json.load(open(path))
                    expires_at = creds.get('expires_at')
                    if expires_at:
                        secs_left = expires_at - time.time()
                        if secs_left < 3600:  # Alert if < 1 hour
                            logger.warning(f"Token {provider} expires in {secs_left}s")
                except Exception as e:
                    logger.error(f"Failed to check {path}: {e}")
        
        await asyncio.sleep(3600)  # Check every hour
```

### 2. Add /settings token-status Command
```python
@settings.command(name="token-status")
async def token_status(interaction: discord.Interaction):
    """Show OAuth token expiry status."""
    # Parse all OAuth credentials
    # Display expiry times
    # Warn if < 1 hour to expiry
    # Suggest manual refresh if needed
```

### 3. Add Manual Refresh Trigger
```python
@settings.command(name="refresh-tokens")
async def refresh_tokens(interaction: discord.Interaction):
    """Manually trigger token refresh."""
    # Reload credentials files
    # Force refresh of expired tokens
    # Report success/failure
```

### 4. Better Error Handling
```python
try:
    response = await rotating_completion(...)
except TokenExpiredError:
    # Specific handling for expired tokens
    # Alert user
    # Try fallback credentials
except AuthenticationError:
    # Specific handling for invalid credentials
    # Ask user to re-authenticate
```

---

## Troubleshooting

### Token Refresh Not Working

**Check 1: Is credentials file writable?**
```bash
ls -l /path/to/credentials/gemini.json
# Should show: -rw------- (600 permissions)
```

**Check 2: Does credentials have refresh_token?**
```bash
grep "refresh_token" /path/to/credentials/gemini.json
# Should output: "refresh_token": "1//0gP..."
```

**Check 3: Can container access the file?**
```bash
docker-compose exec cortana cat /workspace/credentials/gemini.json
# Should output the credentials
```

**Check 4: Is token actually expired?**
```bash
python3 -c "
import json, time
creds = json.load(open('credentials/gemini.json'))
expires_at = creds['expires_at']
secs_left = expires_at - time.time()
print(f'Token expires in {secs_left} seconds')
print('Expired!' if secs_left < 0 else 'Valid')
"
```

### Refresh Fails with "invalid_grant"

**Cause**: Refresh token is revoked or invalid

**Solution**: Re-authenticate to get new refresh token
```bash
# For Gemini CLI: Run OAuth flow again
gcloud auth application-default login

# Credentials will be updated at:
# ~/.config/gcloud/application_default_credentials.json

# Copy to Cortana:
cp ~/.config/gcloud/application_default_credentials.json ./credentials/gemini.json
chmod 600 ./credentials/gemini.json
```

### Refresh Fails with Network Error

**Cause**: Can't reach provider's token endpoint

**Solutions**:
1. Check container networking: `docker-compose logs cortana`
2. Verify internet access: `docker-compose exec cortana curl https://oauth2.googleapis.com`
3. Check proxy configuration if behind corporate proxy

---

## Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| Auto Token Refresh | ✅ Expected | Handled by rotator_library (if credentials valid) |
| Refresh Monitoring | ❌ Not Implemented | Phase 8 enhancement |
| Manual Refresh | ❌ Not Available | Phase 8 enhancement |
| Error Alerting | ❌ Not Implemented | Phase 8 enhancement |
| Fallback on Failure | ✅ Partial | Only if multiple credentials configured |
| Logging | ⚠️ Limited | Generic logs, no specific refresh tracking |

---

**Current Status**: MVP level (delegates to rotator_library, minimal Cortana involvement)

**Recommended Enhancement**: Phase 8 - Add token monitoring and alerting for production use
