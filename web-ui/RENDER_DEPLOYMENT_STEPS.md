# Render.com Deployment Steps

## Prerequisites Checklist

- [ ] Code is pushed to GitHub
- [ ] GitHub repository is public or Render has access
- [ ] You have a Render.com account (free tier is fine)
- [ ] Your CBB API key is ready

## Step-by-Step Deployment

### Step 1: Push Latest Code to GitHub

```bash
# Make sure all changes are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Account & Service

1. **Go to Render.com**: https://render.com
2. **Sign up/Login** (can use GitHub OAuth)
3. **Click "New +"** → **"Web Service"**
4. **Connect your GitHub repository**:
   - Select your repository (`cbbd` or whatever it's named)
   - Render will detect the `render.yaml` file automatically

### Step 3: Configure Service (if not using render.yaml)

If Render doesn't auto-detect `render.yaml`, use these settings:

- **Name**: `cbb-data-generator`
- **Environment**: `Python 3`
- **Region**: Choose closest to you (US East/West, etc.)
- **Branch**: `main`
- **Root Directory**: Leave empty (or `web-ui` if needed)
- **Build Command**: `cd web-ui && pip install -r requirements.txt`
- **Start Command**: `cd web-ui && gunicorn app:app --bind 0.0.0.0:$PORT`

### Step 4: Set Environment Variables

In Render dashboard → Your Service → Environment:

**Required Variables:**

1. **CBB_API_KEY**
   - Value: Your API key from `config/api_config.txt`
   - Mark as: **Secret** ✓
   - This is your College Basketball Data API key

2. **GIT_USER_NAME**
   - Value: Your GitHub username (e.g., `victorres11`)
   - Mark as: **Secret** (optional, but recommended)
   - Used for git commits when pushing generated files

3. **GIT_USER_EMAIL**
   - Value: Your GitHub email
   - Mark as: **Secret** (optional, but recommended)
   - Used for git commits when pushing generated files

4. **RESEND_API_KEY** (Required for email notifications)
   - Value: Your Resend API key
   - Mark as: **Secret** ✓
   - Used for sending email notifications when jobs complete

5. **RESEND_SENDER_EMAIL** (Required for email notifications)
   - Value: `vt@victorres.xyz` (or your verified domain email)
   - Mark as: **Not Secret** (can be public)
   - This is the "from" address for all email notifications
   - Already set in `render.yaml` to `vt@victorres.xyz`

6. **NOTIFICATION_EMAIL** (Required for email notifications)
   - Value: Your email address to receive notifications (e.g., `victorres11@gmail.com`)
   - Mark as: **Secret** (optional, but recommended)
   - This is where job completion emails will be sent

**Optional Variables:**

7. **FLASK_ENV**
   - Value: `production`
   - Already set in `render.yaml`, but you can override if needed

### Step 5: Configure Git for GitHub Pushes

The app needs git configured to push generated files. Render should have git pre-configured, but you may need to:

**Option A: Use Render's Git (Recommended)**
- Render automatically configures git
- Make sure your repository is connected
- The app will use Render's git credentials

**Option B: Add to Build Command (if needed)**
If git isn't working, update `render.yaml` build command:
```yaml
buildCommand: cd web-ui && git config --global user.name "$GIT_USER_NAME" && git config --global user.email "$GIT_USER_EMAIL" && pip install -r requirements.txt
```

### Step 6: Deploy

1. **Click "Create Web Service"**
2. **Wait for build** (2-5 minutes)
3. **Check build logs** for any errors
4. **Your app will be live at**: `https://cbb-data-generator.onrender.com`

### Step 7: Test the Deployment

1. **Visit your Render URL**
2. **Test team search**: Try searching for "UCLA" or "Oregon"
3. **Test data generation**: Select a team and click "Generate Data"
4. **Check logs** in Render dashboard if anything fails

## Troubleshooting

### Build Fails

**Error: "Module not found"**
- Check that `requirements.txt` includes all dependencies
- Verify build command is correct: `cd web-ui && pip install -r requirements.txt`

**Error: "Port already in use"**
- Make sure start command uses `$PORT`: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Runtime Errors

**Error: "API key not found"**
- Verify `CBB_API_KEY` is set in Render environment variables
- Check that it's marked as "Secret" (not visible in logs)
- Restart the service after adding environment variables

**Error: "Teams not loading"**
- Check Render logs for detailed error messages
- Verify API key is valid
- Test API connection manually

**Error: "GitHub push failed"**
- Verify `GIT_USER_NAME` and `GIT_USER_EMAIL` are set
- Check that git is configured in Render environment
- Verify your repository allows pushes (check repository permissions)
- Check Render logs for git error details

### Service Spins Down (Free Tier)

**Issue: Service takes time to start**
- Free tier services spin down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- Consider upgrading to paid tier ($7/month) for always-on service

## Cost Considerations

### Free Tier
- ✅ 750 hours/month free
- ⚠️ Services spin down after 15 minutes of inactivity
- ⚠️ First request after spin-down has ~30 second delay
- ✅ Good for testing and low usage

### Paid Tier ($7/month)
- ✅ Always-on service (no spin-down)
- ✅ Faster response times
- ✅ Better for production use
- ✅ More reliable for users

## Post-Deployment

### Update GitHub Pages URLs

After deployment, update any hardcoded URLs in your code to use the Render URL instead of localhost.

### Monitor Usage

- Check Render dashboard for usage stats
- Monitor logs for errors
- Set up alerts if needed (paid tier)

### Backup Strategy

- Generated JSON files are automatically pushed to GitHub
- Consider setting up automated backups if needed

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test the deployment
3. ✅ Share the URL with users
4. ✅ Monitor for any issues
5. ✅ Consider upgrading to paid tier if usage increases

