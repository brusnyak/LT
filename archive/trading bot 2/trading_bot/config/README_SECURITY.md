# GitGuardian Security Fix

This directory previously contained sensitive credentials that were accidentally committed to Git.

## What was removed:

- `credentials.py` - Contains API keys, tokens, and passwords
- `data.txt` - Contains cTrader implementation with embedded credentials

## How to restore functionality:

1. Copy `credentials.py.template` to `credentials.py`
2. Fill in your actual credentials
3. The file is now gitignored and won't be committed

## Security Note:

If you committed sensitive credentials to a public repository:

1. **Immediately rotate all exposed credentials** (generate new API keys, tokens, passwords)
2. Check GitGuardian alerts for which secrets were exposed
3. Revoke/regenerate:
   - Telegram bot token
   - cTrader credentials
   - All API keys
   - MT5 passwords

## Prevention:

- Never commit files with real credentials
- Always use `.env` files or credential templates
- Use environment variables for sensitive data
- Review `.gitignore` before committing
