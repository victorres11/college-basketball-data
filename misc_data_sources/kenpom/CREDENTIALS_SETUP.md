# KenPom Credentials Setup

## Local Development

For local development, create a credentials file:

1. **Create the credentials file:**
   ```bash
   cd misc_data_sources/kenpom/credentials
   # Create kenpom_credentials.json with your credentials
   ```

2. **Add your credentials:**
   ```json
   {
     "username": "your_email@example.com",
     "password": "your_password"
   }
   ```

3. **The file is gitignored** - it won't be committed to the repository.

## Production (Render.com)

For production deployment, use environment variables instead of the credentials file:

1. **Go to Render Dashboard** → Your Service → Environment

2. **Add these environment variables:**
   - **KENPOM_USERNAME**
     - Value: Your KenPom email/username
     - Mark as: **Secret** ✓
   
   - **KENPOM_PASSWORD**
     - Value: Your KenPom password
     - Mark as: **Secret** ✓

3. **The script will automatically use environment variables** if they're set, otherwise it falls back to the credentials file.

## How It Works

The `kenpom_data.py` script checks for credentials in this order:
1. Environment variables (`KENPOM_USERNAME`, `KENPOM_PASSWORD`) - for production
2. Credentials file (`kenpom_credentials.json`) - for local development

This ensures:
- ✅ Production uses secure environment variables
- ✅ Local development can use a file
- ✅ No credentials are committed to git
