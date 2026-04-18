# Gmail OAuth setup — from zero to `gmail_credentials.json`

One-time, ~10 minutes. You only do this once per Gmail account.

## 1. Google Cloud Console project (3 min)

1. Go to **https://console.cloud.google.com/**.
2. Top-left project dropdown → **New Project**.
3. Name: `autosapien-ai-employee`. Leave org as default. Click **Create**.
4. Wait ~30 s for the project to provision, then switch to it from the dropdown.

## 2. Enable the Gmail API (1 min)

1. Hamburger menu (top-left) → **APIs & Services → Library**.
2. Search for **Gmail API**. Click the result.
3. Click **Enable**. Wait ~20 seconds.

## 3. OAuth consent screen (3 min)

1. **APIs & Services → OAuth consent screen**.
2. User Type: **External**. Click **Create**.
3. Fill in the required fields only:
   - App name: `autosapien AI Employee (dev)`
   - User support email: **dilawar.gopang@gmail.com**
   - Developer contact: **dilawar.gopang@gmail.com**
4. Click **Save and Continue** through **Scopes** (skip), **Test users**, and **Summary**.
5. On the **Test users** step, add `dilawar.gopang@gmail.com` as a test user. Save.
6. You do **NOT** need to submit for verification — the app will stay in "testing" mode and work for up to 100 test users.

## 4. OAuth client ID (2 min)

1. **APIs & Services → Credentials → + Create Credentials → OAuth client ID**.
2. Application type: **Desktop app**.
3. Name: `autosapien-ai-employee-desktop`.
4. Click **Create**.
5. A dialog shows **Client ID** and **Client Secret**. Click **Download JSON**.
6. Rename the downloaded file to **`gmail_credentials.json`** and move it to:

   ```
   C:\Users\TechTiesIbrahim\hackathon0_by_dilawar\secrets\gmail_credentials.json
   ```

   (Create the `secrets/` folder if it doesn't exist.)

## 5. Mint the token (1 min)

From the repo root:

```powershell
# Ensure secrets/ exists and the credentials file is in place
ls secrets\gmail_credentials.json    # should show the file

# Opt in and run the watcher once to trigger OAuth
$env:ENABLE_GMAIL_WATCHER = "true"
uv run python watchers\gmail_watcher.py
```

A browser window opens. Sign in as **dilawar.gopang@gmail.com**. You'll see
"Google hasn't verified this app" — click **Advanced → Go to autosapien AI
Employee (unsafe)**. That warning is expected for a testing-mode OAuth app.

After you grant access, the browser says "Authentication complete — you
may close this tab" and a file appears at:

```
secrets\gmail_token.json
```

**Ctrl+C** the watcher. The token is now minted and reusable.

## 6. Verify (30 s)

```powershell
uv run python -c "from watchers.gmail_watcher import GmailWatcher; w = GmailWatcher('./AI_Employee_Vault'); items = list(w.check_for_updates()); print('Unread items found:', len(items))"
```

If that prints a non-zero number (or 0 if your inbox is clean), the
integration works.

## Troubleshooting

**"access_denied" error in the browser**
You're not listed as a test user. Go back to OAuth consent screen →
Test users → add your email.

**"redirect_uri_mismatch"**
You created a "Web application" client instead of "Desktop app". Redo
step 4 with type = Desktop app.

**"invalid_grant" / token refresh fails after a few days**
Testing-mode tokens expire after ~7 days. Delete
`secrets/gmail_token.json` and re-run the watcher to re-auth.
