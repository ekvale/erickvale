"""
Script to upgrade CKEditor to 4.25.1-lts
Note: CKEditor 4.25.1-lts requires a commercial license.
This script helps download and install the files.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CKEDITOR_DIR = BASE_DIR / 'staticfiles' / 'ckeditor' / 'ckeditor'
BACKUP_DIR = BASE_DIR / 'staticfiles' / 'ckeditor' / 'ckeditor_backup_4.22.1'

def backup_current_version():
    """Backup current CKEditor installation"""
    if CKEDITOR_DIR.exists():
        print(f"Backing up current CKEditor to {BACKUP_DIR}")
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(CKEDITOR_DIR, BACKUP_DIR)
        print("✓ Backup complete")
        return True
    else:
        print("⚠ No existing CKEditor installation found")
        return False

def check_npm():
    """Check if npm is available"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, check=True)
        print(f"✓ npm found: {result.stdout.strip()}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("✗ npm not found")
        return False

def install_ckeditor_npm():
    """Download CKEditor using npm (recommended method)"""
    print("\nInstalling CKEditor 4.25.1-lts via npm...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # Initialize npm and install CKEditor
        print("Initializing npm package...")
        subprocess.run(['npm', 'init', '-y'], check=True, capture_output=True, text=True)
        
        print("Installing ckeditor4@4.25.1-lts...")
        subprocess.run(['npm', 'install', 'ckeditor4@4.25.1-lts'], check=True, text=True)
        
        # Copy files
        source_dir = Path(temp_dir) / 'node_modules' / 'ckeditor4'
        if source_dir.exists():
            print(f"Copying CKEditor files from {source_dir} to {CKEDITOR_DIR}")
            if CKEDITOR_DIR.exists():
                shutil.rmtree(CKEDITOR_DIR)
            shutil.copytree(source_dir, CKEDITOR_DIR)
            print("✓ CKEditor 4.25.1-lts installed successfully")
            return True
        else:
            print("✗ Error: CKEditor files not found in node_modules")
            return False
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing via npm: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False
    finally:
        os.chdir(original_dir)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def main():
    print("=" * 60)
    print("CKEditor Upgrade Script")
    print("=" * 60)
    print("Upgrading from CKEditor 4.22.1 to 4.25.1-lts")
    print("\n⚠ IMPORTANT: CKEditor 4.25.1-lts requires a commercial license.")
    print("   Please ensure you have a valid license before proceeding.")
    print("   Visit: https://ckeditor.com/pricing/\n")
    
    response = input("Do you have a valid CKEditor 4 LTS license? (yes/no): ")
    if response.lower() != 'yes':
        print("\n" + "=" * 60)
        print("CKEditor 4.25.1-lts requires a commercial license.")
        print("Please visit https://ckeditor.com/pricing/ to obtain a license.")
        print("\nAlternatives:")
        print("1. Continue using CKEditor 4.22.1 (⚠ not recommended - security issues)")
        print("2. Migrate to CKEditor 5 (open-source, actively maintained)")
        print("=" * 60)
        return
    
    # Backup current version
    print("\n" + "-" * 60)
    print("Step 1: Backing up current installation")
    print("-" * 60)
    backup_current_version()
    
    # Check for npm
    print("\n" + "-" * 60)
    print("Step 2: Checking prerequisites")
    print("-" * 60)
    if not check_npm():
        print("\n" + "=" * 60)
        print("npm is required but not found.")
        print("\nPlease install Node.js and npm:")
        print("  - Windows: Download from https://nodejs.org/")
        print("  - Linux: sudo apt install nodejs npm")
        print("  - Mac: brew install node")
        print("\nOr follow manual installation steps in UPGRADE_CKEDITOR.md")
        print("=" * 60)
        return
    
    # Install CKEditor
    print("\n" + "-" * 60)
    print("Step 3: Installing CKEditor 4.25.1-lts")
    print("-" * 60)
    if install_ckeditor_npm():
        print("\n" + "=" * 60)
        print("✓ Upgrade complete!")
        print("=" * 60)
        print(f"\nBackup saved to: {BACKUP_DIR}")
        print("\nNext steps:")
        print("1. Run: python manage.py collectstatic")
        print("2. Test your CKEditor functionality")
        print("3. Verify version in browser console: CKEDITOR.version")
        print("4. If everything works, you can delete the backup directory")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Automatic installation failed.")
        print("=" * 60)
        print("\nManual installation steps:")
        print("1. Install Node.js and npm if not already installed")
        print("2. Run: npm install ckeditor4@4.25.1-lts")
        print("3. Copy files from node_modules/ckeditor4 to staticfiles/ckeditor/ckeditor/")
        print("4. Run: python manage.py collectstatic")
        print("\nSee UPGRADE_CKEDITOR.md for detailed instructions.")
        print("=" * 60)

if __name__ == '__main__':
    main()

