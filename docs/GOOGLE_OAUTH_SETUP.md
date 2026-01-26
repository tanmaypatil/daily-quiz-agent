# Google OAuth Setup Guide

Complete guide to set up Google OAuth for the CLAT Quiz application.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page
3. Click "New Project"
4. Enter project name: `clat-quiz` (or any name you prefer)
5. Click "Create"
6. Wait for the project to be created, then select it

## Step 2: Enable Required APIs

1. In the left sidebar, go to **APIs & Services** > **Library**
2. Search for and enable these APIs:
   - **Google+ API** (for user profile info)
   - Or search for "People API" and enable it

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** (unless you have Google Workspace, then choose Internal)
3. Click "Create"

### Fill in the consent screen details:

**App Information:**
- App name: `CLAT Daily Quiz`
- User support email: Your email
- App logo: (optional)

**App Domain:**
- Leave blank for now (localhost doesn't need these)

**Developer contact information:**
- Enter your email address

4. Click "Save and Continue"

### Scopes:
1. Click "Add or Remove Scopes"
2. Select these scopes:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
3. Click "Update"
4. Click "Save and Continue"

### Test Users (Important for External apps):
1. Click "Add Users"
2. Add the email addresses that will test the app (including yours)
3. Click "Save and Continue"

4. Review the summary and click "Back to Dashboard"

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click "Create Credentials" > **OAuth client ID**
3. Select Application type: **Web application**
4. Name: `CLAT Quiz Web Client`

### Authorized JavaScript origins:
Add these URIs:
```
http://localhost:5000
```

### Authorized redirect URIs:
Add these URIs:
```
http://localhost:5000/auth/callback
```

5. Click "Create"

## Step 5: Copy Your Credentials

After creating, you'll see a popup with:
- **Client ID**: `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxx`

Copy these values!

## Step 6: Update Your .env File

Open `/Users/tanmaypatil/daily-quiz-agent/.env` and update:

```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 7: Add Authorized Users (Optional)

If you want to restrict access to specific Gmail accounts:

```env
AUTHORIZED_EMAILS=daughter@gmail.com,yourother@gmail.com
```

Leave empty to allow anyone to log in.

## Step 8: Add Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Add to `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Make sure the redirect URI in Google Console exactly matches: `http://localhost:5000/auth/callback`
- Check for trailing slashes

### "Error 403: access_denied"
- For External apps in testing mode, add your email to "Test users" in OAuth consent screen

### "redirect_uri_mismatch"
- The redirect URI in your request doesn't match the ones configured in Google Console
- Make sure BASE_URL in .env is `http://localhost:5000` (no trailing slash)

## Production Setup

When deploying to `quiz.germanwakad.click`:

1. Go back to Google Cloud Console > Credentials
2. Edit your OAuth client
3. Add production URIs:

**Authorized JavaScript origins:**
```
https://quiz.germanwakad.click
```

**Authorized redirect URIs:**
```
https://quiz.germanwakad.click/auth/callback
```

4. Update `.env` on server:
```env
BASE_URL=https://quiz.germanwakad.click
```

## Quick Checklist

- [ ] Created Google Cloud Project
- [ ] Enabled required APIs
- [ ] Configured OAuth consent screen
- [ ] Added test users (for External apps)
- [ ] Created OAuth credentials (Web application)
- [ ] Added `http://localhost:5000` to authorized origins
- [ ] Added `http://localhost:5000/auth/callback` to redirect URIs
- [ ] Copied Client ID and Client Secret to `.env`
- [ ] Added Anthropic API key to `.env`
