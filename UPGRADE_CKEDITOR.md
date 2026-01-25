# Upgrading CKEditor to 4.25.1-lts

## Important Note

CKEditor 4.25.1-lts requires a **commercial license**. CKEditor 4 reached end-of-life for open-source support on June 30, 2023. The LTS (Long-Term Support) versions are part of the Extended Support Model and require a valid license.

## Prerequisites

1. **Valid CKEditor 4 LTS License** - You must have a commercial license to use CKEditor 4.25.1-lts
2. **Node.js and npm** - Required to install CKEditor via npm

## Method 1: Using npm (Recommended)

1. Install Node.js and npm if not already installed:
   ```bash
   # Check if installed
   node --version
   npm --version
   ```

2. Install CKEditor 4.25.1-lts:
   ```bash
   npm install ckeditor4@4.25.1-lts
   ```

3. Copy the files to your Django staticfiles directory:
   ```bash
   # On Windows (PowerShell)
   Copy-Item -Path "node_modules\ckeditor4\*" -Destination "staticfiles\ckeditor\ckeditor\" -Recurse -Force
   
   # On Linux/Mac
   cp -r node_modules/ckeditor4/* staticfiles/ckeditor/ckeditor/
   ```

4. Run Django collectstatic:
   ```bash
   python manage.py collectstatic --noinput
   ```

## Method 2: Manual Download

1. Download CKEditor 4.25.1-lts from:
   - https://ckeditor.com/cke4/builder (custom build)
   - Or use the npm package: `npm pack ckeditor4@4.25.1-lts`

2. Extract the files to `staticfiles/ckeditor/ckeditor/`

3. Run Django collectstatic:
   ```bash
   python manage.py collectstatic --noinput
   ```

## Method 3: Using the Upgrade Script

1. Run the upgrade script:
   ```bash
   python upgrade_ckeditor.py
   ```

2. Follow the prompts

## Verification

After upgrading, verify the version:

1. Check the CKEditor version in the browser console:
   ```javascript
   console.log(CKEDITOR.version);
   ```
   Should show: `4.25.1-lts`

2. Or check the file directly:
   ```bash
   # On Linux/Mac
   head -n 5 staticfiles/ckeditor/ckeditor/ckeditor.js | grep version
   
   # On Windows (PowerShell)
   Get-Content staticfiles\ckeditor\ckeditor\ckeditor.js -Head 5 | Select-String "version"
   ```

## Backup

The upgrade script automatically backs up your current CKEditor installation to:
`staticfiles/ckeditor/ckeditor_backup_4.22.1/`

You can restore it if needed by copying the backup back.

## Alternative: Migrate to CKEditor 5

If you don't have a commercial license, consider migrating to CKEditor 5, which is:
- Open-source (GPL or commercial license)
- Actively maintained
- Modern architecture
- Better security

However, note that CKEditor 5 is a completely different editor and requires code changes.

## Server Update

After upgrading locally, update your server:

1. Push changes to GitHub
2. On server:
   ```bash
   cd /home/erickvale/erickvale
   git pull origin main
   npm install ckeditor4@4.25.1-lts  # If using npm method
   python manage.py collectstatic --noinput
   sudo systemctl restart gunicorn
   ```



