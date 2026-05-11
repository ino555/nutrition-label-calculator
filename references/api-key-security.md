# API Key Security Guide

## Getting Your USDA FoodData Central API Key

1. Go to https://fdc.nal.usda.gov/api-guide.html
2. Click "Get an API Key"
3. Fill in your name and email — the key arrives instantly by email
4. The key is free and has no request limits for reasonable use

## Setting Up Your Key (One-Time)

### Option A — .claude/settings.local.json (Recommended)

Create or edit `.claude/settings.local.json` in your project directory:

```json
{
  "env": {
    "FDC_API_KEY": "YOUR_ACTUAL_KEY_HERE"
  }
}
```

This file is automatically loaded by Claude Code for this project only.

**Critical:** Add this file to `.gitignore` immediately:
```
.claude/settings.local.json
```

### Option B — System Environment Variable

Windows PowerShell (permanent, survives restarts):
```powershell
[System.Environment]::SetEnvironmentVariable("FDC_API_KEY", "YOUR_KEY", "User")
```

macOS/Linux (add to `~/.zshrc` or `~/.bashrc`):
```bash
export FDC_API_KEY="YOUR_KEY"
```
Then run: `source ~/.zshrc`

### Option C — Session Only (temporary)

Windows PowerShell:
```powershell
$env:FDC_API_KEY = "YOUR_KEY"
```

macOS/Linux:
```bash
export FDC_API_KEY="YOUR_KEY"
```

## Security Rules

- **NEVER** paste your API key directly into any Python script, SKILL.md, or any file that might be committed to git
- **NEVER** share your key in chat messages, issues, or pull requests
- The key should only ever exist in: environment variables, `.claude/settings.local.json`, or a `.env` file that is gitignored

## If You Accidentally Committed Your Key

1. Revoke the key immediately at https://fdc.nal.usda.gov
2. Request a new key
3. Remove from git history using BFG Repo Cleaner:
   ```bash
   java -jar bfg.jar --replace-text passwords.txt my-repo.git
   ```
4. Add the file to `.gitignore` before re-committing

## Verifying .gitignore

Check your `.gitignore` includes these entries:
```bash
grep -E "\.env|settings\.local" .gitignore
```

Expected output should show `.env` and `settings.local.json` are ignored.
