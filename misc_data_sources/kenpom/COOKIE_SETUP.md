# KenPom Cookie Setup Guide

## Why Use Cookies?

If you're getting 403 Forbidden errors when trying to log in with username/password, KenPom is likely blocking automated login attempts from your server's IP address. Using cookies bypasses the login process entirely and avoids this issue.

## How to Extract Cookies

### Method 1: Chrome/Edge Browser

1. **Log in to KenPom** in your browser:
   - Go to https://kenpom.com
   - Log in with your username and password
   - Make sure you're logged in and can access protected pages

2. **Open Developer Tools**:
   - Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Or right-click on the page → "Inspect"

3. **Go to Application/Storage Tab**:
   - Click the **"Application"** tab (Chrome) or **"Storage"** tab (Firefox)
   - In the left sidebar, expand **"Cookies"**
   - Click on **"https://kenpom.com"**

4. **Find the PHPSESSID cookie**:
   - Look for a cookie named `PHPSESSID`
   - Copy the **Value** (it will be a long string of letters and numbers)

### Method 2: Firefox Browser

1. Log in to KenPom
2. Press `F12` to open Developer Tools
3. Go to **"Storage"** tab
4. Expand **"Cookies"** → **"https://kenpom.com"**
5. Find `PHPSESSID` and copy its value

### Method 3: Browser Extension

You can use a browser extension like "Cookie Editor" to easily view and copy cookies.

## Setting Up Cookies in Production (Render.com)

1. **Go to Render Dashboard**:
   - Navigate to your service → **Environment**

2. **Remove or keep username/password** (optional):
   - You can keep `KENPOM_USERNAME` and `KENPOM_PASSWORD` as backup
   - Or remove them if you prefer cookie-only auth

3. **Add the cookie environment variable**:
   - **Key**: `KENPOM_PHPSESSID`
   - **Value**: Paste the PHPSESSID cookie value you copied
   - **Mark as Secret**: ✓ (recommended)

4. **Save and redeploy**:
   - Click "Save Changes"
   - Render will automatically redeploy

## Cookie Persistence

### How Long Do Cookies Last?

- **PHPSESSID cookies** are typically **session cookies** that expire when:
  - You log out
  - Your browser session ends (if the site doesn't use persistent sessions)
  - The server invalidates the session (usually after inactivity)

- **KenPom's specific behavior**:
  - Cookies may last **several days to weeks** if you stay logged in
  - They may expire after **inactivity** (varies by site)
  - They will definitely expire if you **manually log out**

### When Do You Need to Update?

You'll need to update the cookie when:
- ✅ You get authentication errors in the logs
- ✅ The cookie has expired (usually after days/weeks of inactivity)
- ✅ You've logged out of KenPom in your browser
- ✅ KenPom has invalidated your session

### How to Check if Cookie is Still Valid

The generator will log errors if the cookie is invalid. You'll see messages like:
- `Authentication failed - redirected to login`
- `Page appears to be behind paywall`

If you see these, extract a fresh cookie and update the environment variable.

## Priority Order

The script checks credentials in this order:

1. **KENPOM_PHPSESSID** (cookie) - **Recommended if login is blocked**
2. **KENPOM_USERNAME + KENPOM_PASSWORD** (username/password)
3. **Local credentials file** (for development)

If `KENPOM_PHPSESSID` is set, it will use that and skip login entirely.

## Troubleshooting

### Cookie Not Working?

1. **Verify the cookie value**:
   - Make sure you copied the entire value (no spaces, no truncation)
   - The value should be a long alphanumeric string

2. **Check if you're still logged in**:
   - Go to kenpom.com in your browser
   - If you see a login page, your session expired
   - Log in again and extract a fresh cookie

3. **Verify environment variable**:
   - In Render.com, check that `KENPOM_PHPSESSID` is set correctly
   - Make sure there are no extra spaces or quotes

4. **Check the logs**:
   - Look for `[KENPOM] Using cookie-based authentication` message
   - If you see authentication errors, the cookie may be expired

## Security Notes

- ✅ Cookies are stored as **Secret** environment variables in Render.com
- ✅ Cookies are **not committed** to git (they're in environment variables)
- ⚠️ **Don't share your PHPSESSID cookie** - it gives access to your account
- ⚠️ If your cookie is compromised, log out and generate a new one

