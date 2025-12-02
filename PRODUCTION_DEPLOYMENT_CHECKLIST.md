# Production Deployment Checklist

## Pre-Deployment

### ✅ Code Changes
- [x] KenPom integration added to generator
- [x] Credentials handling supports environment variables
- [x] Google Apps Script functions created
- [x] Status tracking includes KenPom
- [x] Files reorganized (quadrants → misc_data_sources)
- [x] All import paths updated

### 📋 Before Pushing

1. **Review git status:**
   ```bash
   git status
   ```

2. **Files to commit:**
   - `misc_data_sources/` (new folder structure)
   - `web-ui/generator.py` (KenPom integration)
   - `web-ui/render.yaml` (environment variables)
   - `apps-script/google-apps-script-cbbd.js` (new functions)
   - `apps-script/Code.gs` (synced)
   - `.gitignore` (updated)

3. **Files that should NOT be committed:**
   - `misc_data_sources/kenpom/credentials/kenpom_credentials.json` (gitignored)
   - `misc_data_sources/kenpom/output/*.html` (test files, gitignored)
   - `misc_data_sources/kenpom/output/*_structured.json` (test files, gitignored)

## Production Setup (Render.com)

### Required Environment Variables

After deploying, add these in Render Dashboard → Your Service → Environment:

1. **KENPOM_USERNAME**
   - Value: Your KenPom email/username
   - Mark as: **Secret** ✓
   - Required for KenPom data fetching

2. **KENPOM_PASSWORD**
   - Value: Your KenPom password
   - Mark as: **Secret** ✓
   - Required for KenPom data fetching

### Existing Environment Variables (verify these are set):
- `CBB_API_KEY` - College Basketball Data API key
- `GIT_USER_NAME` - GitHub username (for file pushes)
- `GIT_USER_EMAIL` - GitHub email (for file pushes)
- `S3_BUCKET_NAME` - S3 bucket name (if using S3)
- `AWS_ACCESS_KEY_ID` - AWS access key (if using S3)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (if using S3)

## Post-Deployment Testing

1. **Test KenPom Integration:**
   - Generate data for a team (e.g., UCLA or Oregon)
   - Verify KenPom status appears in status table
   - Check that KenPom data is included in generated JSON

2. **Verify Status Table:**
   - Should show "KenPom Data" with status (success/failed/skipped)
   - Should display category count on success

3. **Test Google Apps Script Functions:**
   - `GET_KENPOM_REPORT_TABLE(url)` - Full table
   - `GET_KENPOM_ADJ_EFFICIENCY(url)` - Adj. Efficiency
   - `GET_KENPOM_ADJ_TEMPO(url)` - Adj. Tempo
   - `GET_KENPOM_FOUR_FACTORS(url)` - Four Factors
   - `GET_KENPOM_CATEGORY(url, "Category Name")` - Specific category

## Troubleshooting

### KenPom Data Not Appearing

1. **Check credentials:**
   - Verify `KENPOM_USERNAME` and `KENPOM_PASSWORD` are set in Render
   - Check that they're marked as "Secret"
   - Restart the service after adding variables

2. **Check logs:**
   - Look for `[GENERATOR] KenPom scraper import: OK`
   - Look for `[GENERATOR] Fetching KenPom data...`
   - Check for any error messages

3. **Verify subscription:**
   - Make sure your KenPom subscription is active
   - Test login manually in browser

### Status Shows "Skipped"

- This means the scraper couldn't be imported
- Check that `misc_data_sources/kenpom/scripts/kenpom_data.py` exists
- Verify all dependencies are installed (`requests`, `beautifulsoup4`)

## Notes

- KenPom data fetching is **non-blocking** - if it fails, generation continues
- The status table will show the result (success/failed/skipped)
- All 32 categories from the report table are included in the JSON output

