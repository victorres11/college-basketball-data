# Deployment Guide

## Quick Start

### Local Testing

1. **Set environment variable:**
   ```bash
   export CBB_API_KEY=your_api_key_here
   ```

2. **Run the app:**
   ```bash
   cd web-ui
   python app.py
   ```

3. **Test in browser:**
   - Open http://localhost:5000
   - Search for a team (e.g., "Oregon")
   - Select the team
   - Click "Generate Data"
   - Wait 2-3 minutes for completion

## Render.com Deployment

### Step 1: Prepare Repository

Make sure your code is pushed to GitHub:
```bash
git add web-ui/
git commit -m "Add web UI"
git push
```

### Step 2: Create Render Service

1. Go to https://render.com and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render should auto-detect `render.yaml` - if not, use these settings:

**Basic Settings:**
- **Name**: `cbb-data-generator`
- **Environment**: `Python 3`
- **Region**: Choose closest to you
- **Branch**: `main`

**Build & Deploy:**
- **Build Command**: `cd web-ui && pip install -r requirements.txt`
- **Start Command**: `cd web-ui && gunicorn app:app --bind 0.0.0.0:$PORT`

### Step 3: Environment Variables

Add these in Render dashboard → Environment:

1. **CBB_API_KEY** (Required)
   - Your College Basketball Data API key
   - Mark as "Secret"

2. **GIT_USER_NAME** (Required for GitHub push)
   - Your GitHub username
   - Example: `victorres11`

3. **GIT_USER_EMAIL** (Required for GitHub push)
   - Your GitHub email
   - Example: `your-email@example.com`

4. **RESEND_API_KEY** (Required for email notifications)
   - Your Resend API key
   - Mark as "Secret"
   - Used for sending email notifications when jobs complete

5. **RESEND_SENDER_EMAIL** (Required for email notifications)
   - Value: `vt@victorres.xyz` (or your verified domain email)
   - This is the "from" address for all email notifications
   - Already set in `render.yaml` to `vt@victorres.xyz`

6. **NOTIFICATION_EMAIL** (Required for email notifications)
   - Your email address to receive notifications
   - Example: `victorres11@gmail.com`
   - Mark as "Secret" (optional)

7. **FLASK_ENV** (Optional)
   - Set to `production`

### Step 4: Git Configuration

The app needs git configured to push files. Options:

**Option A: Use Render's Git (Recommended)**
- Render automatically has git configured
- Make sure your repository is connected
- The app will use Render's git credentials

**Option B: Configure in Build Command**
Add to build command:
```bash
cd web-ui && git config --global user.name "$GIT_USER_NAME" && git config --global user.email "$GIT_USER_EMAIL" && pip install -r requirements.txt
```

### Step 5: Deploy

1. Click "Create Web Service"
2. Wait for build to complete
3. Your app will be live at: `https://your-app-name.onrender.com`

## Troubleshooting

### "GitHub push failed"
- Check that `GIT_USER_NAME` and `GIT_USER_EMAIL` are set
- Verify git is configured in Render environment
- Check that your repository allows pushes from Render

### "API key not found"
- Verify `CBB_API_KEY` is set in Render environment variables
- Make sure it's marked as "Secret" (not visible in logs)

### "Teams not loading"
- Check API connection
- Verify API key is valid
- Check Render logs for errors

### "Generation fails"
- Check Render logs for detailed error messages
- Verify API key has sufficient permissions
- Check that team name matches API format (lowercase)

## Cost Considerations

**Render Free Tier:**
- 750 hours/month free
- Services spin down after 15 minutes of inactivity
- Good for low usage/testing

**Render Paid ($7/month):**
- Always-on service
- Better for production use
- No spin-down delays

## Alternative Hosting

### Railway
- Similar to Render
- Good free tier
- Easy deployment

### Fly.io
- Good for background jobs
- Generous free tier
- More complex setup

### Heroku
- Easy deployment
- More expensive
- Good documentation

