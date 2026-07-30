# n8n setup — Google Drive credential & folder ID

Detailed walkthrough for the two steps that trip people up on self-hosted n8n.

---

## Part 1 — Google Drive OAuth2 credential

### Read this first: you need a Google Cloud project

n8n Cloud has a one-click "Sign in with Google" (Managed OAuth2). **Self-hosted
does not.** You must create your own Google Cloud OAuth app and paste its Client
ID / Secret into n8n. It's about 10 minutes, one time.

### ⚠️ The seven-day token trap

This one matters specifically because your workflow runs **weekly**.

If your OAuth consent screen is set to **External** + **Testing** publishing
status, Google expires the refresh token after **7 days**. Your Monday scrape
would work once, then silently fail every week after with an auth error.

Pick one of these before you start:

| Your Google account | Do this |
|---|---|
| Google Workspace (a work domain) | Set audience to **Internal** — tokens don't expire |
| Personal @gmail.com (your case) | Set **External**, then **publish the app** (Audience → Publish app). Unverified apps that only request Drive scope for personal use stay working; you'll click through a "not verified" warning once |

Leaving it on External + Testing is the single most common reason a scheduled
n8n Google workflow dies after a week.

---

### Step 1 — Create the Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com), sign in
   as **nicolas.wajs@gmail.com** (the account that owns the `JobApplications`
   folder — this matters).
2. Project dropdown in the top bar → **New project**.
3. Name it something recognizable: `n8n-job-search`.
4. **Create**, then make sure that project is selected in the top bar.

### Step 2 — Enable the Google Drive API

1. Left menu → **APIs & Services** → **Library**.
2. Search `Google Drive API`.
3. Select it → **Enable**.

That's the only API this workflow needs.

### Step 3 — Configure the OAuth consent screen

1. Left menu → **APIs & Services** → **OAuth consent screen**.
2. **Get started**.
3. **App name**: `n8n job search`. **User support email**: your address. → Next.
4. **Audience**: **External** (for a personal Gmail account). → Next.
5. Contact email: your address. → Next.
6. Accept the User Data Policy → **Continue** → **Create**.
7. Left menu → **Branding** → **Authorized domains** → **Add domain**.
   - Running n8n locally on `localhost`? **Skip this** — localhost needs no
     authorized domain.
   - Running n8n on a real domain? Add that domain here.
8. **Save**.

**Now deal with the 7-day trap:** go to **Audience** in the left menu.
- Click **Publish app** and confirm. Status changes from Testing to In production.
- If you'd rather stay in Testing, add `nicolas.wajs@gmail.com` under
  **Test users** — but expect to re-authenticate every 7 days.

### Step 4 — Start the n8n credential (to get the redirect URL)

Do this *before* creating the Google client, because you need to copy a URL out
of n8n.

1. In n8n: **Credentials** → **Add credential** → search **Google Drive OAuth2 API**.
2. The credential panel shows an **OAuth Redirect URL** near the top.
   Copy it exactly. Locally it looks like:

   ```
   http://localhost:5678/rest/oauth2-credential/callback
   ```

   Leave this panel open.

> **Localhost is fine.** Google explicitly permits `localhost` redirect URIs for
> development — you do **not** need HTTPS, a public domain, or a tunnel to make
> this work on your own machine.
>
> If n8n runs on a server or in Docker behind a domain, set the `WEBHOOK_URL`
> environment variable to that public address (e.g.
> `WEBHOOK_URL=https://n8n.yourdomain.com`) and restart n8n — otherwise n8n
> generates a redirect URL Google can't reach. The path
> `/rest/oauth2-credential/callback` stays the same.

### Step 5 — Create the Google OAuth client

1. Back in Google Cloud → **APIs & Services** → **Credentials**.
2. **+ Create credentials** → **OAuth client ID**.
3. **Application type**: **Web application**.
4. **Name**: `n8n`.
5. **Authorized redirect URIs** → **+ Add URI** → paste the URL you copied from
   n8n. It must match **character for character** — protocol, port, and path
   included. `http` ≠ `https`, and a trailing slash breaks it.
6. **Create**.
7. A modal appears with **Client ID** and **Client Secret**. Keep it open.

### Step 6 — Finish in n8n

1. Paste the **Client ID** into the n8n credential.
2. Paste the **Client Secret**.
3. Click **Sign in with Google**.
4. Choose **nicolas.wajs@gmail.com**.
5. If you see "Google hasn't verified this app": **Advanced** → **Go to n8n
   (unsafe)**. This is your own app — the warning is expected for unverified
   personal apps.
6. Grant Drive access. The n8n panel should show **Connected**.
7. **Save**, and rename it to `Google Drive account` so it matches what the
   imported workflow expects.

### If it fails

| Error | Cause | Fix |
|---|---|---|
| `redirect_uri_mismatch` | URL in Google ≠ URL in n8n | Re-copy from n8n, repaste in Google. Check protocol, port, no trailing slash |
| `invalid_client` | Client ID/Secret wrong | Recopy both from Google; watch for a stray leading space |
| `access_denied` | App in Testing, you're not a test user | Publish the app, or add yourself under Audience → Test users |
| Works, then breaks after a week | The 7-day trap | Publish the app (see above) |

---

## Part 2 — Check the Drive folder ID

The upload node needs to know *which* folder to drop the weekly JSON into.

### Where the ID comes from

Open the folder in Google Drive and look at the URL:

```
https://drive.google.com/drive/folders/1kHLEHtByGC33M-75rw-4zV7XwTgJCx-E
                                       └─────────── this is the ID ──────────┘
```

Your `JobApplications` folder ID is:

```
1kHLEHtByGC33M-75rw-4zV7XwTgJCx-E
```

It's already set in two places, and they must agree:

| File | Field |
|---|---|
| `config/search-profile.yaml` | `output.drive_folder_id` |
| `n8n/weekly-job-scrape.json` | the **Upload to Drive** node's `folderId` |

### Verify it in the n8n UI

1. Open the imported workflow.
2. Click the **Upload to Drive — JobApplications** node.
3. Check three fields:
   - **Credential**: the Google Drive credential you just made
   - **Drive**: `My Drive`
   - **Folder**: switch the selector to **By ID** and confirm it reads
     `1kHLEHtByGC33M-75rw-4zV7XwTgJCx-E`

   Or switch the selector to **From list** and pick `JobApplications` directly —
   n8n resolves the ID for you. Once the credential works, this is the easier
   route and removes any chance of a typo.

### If you ever move or recreate the folder

Update the YAML first, then push it into the workflow:

```bash
# edit output.drive_folder_id in config/search-profile.yaml, then:
python3 pipeline/config_to_n8n.py --write
```

`config_to_n8n.py` syncs the folder ID into the workflow JSON, so the YAML stays
the single source of truth. Re-import the workflow into n8n afterwards.

---

## Final check before activating

Run the workflow manually once (**Execute Workflow**), then:

1. **Apify node** — should return job items, not an auth error.
2. **Filter & Dedupe node** — open the output, check `stats`. The kept count and
   the `dropped_sample` list should look sensible.
3. **Upload node** — a `jobs-YYYY-MM-DD.json` file should appear in
   `JobApplications` in Drive. Go look at it.
4. **Run Summary node** — prints the human-readable breakdown.

Only once a file actually lands in Drive should you toggle the workflow
**Active**. A scheduled workflow that fails silently is worse than no workflow.

Sources:
- [Google OAuth2 single service — n8n Docs](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service)
- [Google OAuth2 generic — n8n Docs](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic)
