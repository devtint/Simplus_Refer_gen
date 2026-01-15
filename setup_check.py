#!/usr/bin/env python3
"""
Quick setup script for Simplus Bot
Run this to verify your setup before deployment
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    req_text = "(Required)" if required else "(Optional)"
    print(f"{status} {filepath} {req_text}")
    return exists

def check_env_var(var_name, required=True):
    """Check if environment variable is set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    value = os.getenv(var_name)
    has_value = value and value != f"your_{var_name.lower()}_here" and value != "change_this_password"
    status = "✅" if has_value else "❌"
    req_text = "(Required)" if required else "(Optional)"
    print(f"{status} {var_name} {req_text}")
    return has_value

def main():
    print("🔍 Simplus Bot Setup Verification\n")
    
    all_good = True
    
    # Check required files
    print("📁 Checking Files:")
    all_good &= check_file_exists("app.py")
    all_good &= check_file_exists("automated.py")
    all_good &= check_file_exists("requirements.txt")
    all_good &= check_file_exists(".env")
    all_good &= check_file_exists(".gitignore")
    check_file_exists("config.json", required=False)
    check_file_exists("session.session", required=False)
    print()
    
    # Check templates
    print("📄 Checking Templates:")
    all_good &= check_file_exists("templates/login.html")
    all_good &= check_file_exists("templates/dashboard.html")
    all_good &= check_file_exists("templates/settings.html")
    print()
    
    # Check environment variables
    print("🔧 Checking Environment Variables:")
    all_good &= check_env_var("API_ID")
    all_good &= check_env_var("API_HASH")
    all_good &= check_env_var("PHONE_NUMBER")
    all_good &= check_env_var("NATION_CODE")
    check_env_var("INVITATION_CODES", required=False)
    all_good &= check_env_var("WEB_USERNAME")
    all_good &= check_env_var("WEB_PASSWORD")
    check_env_var("KEEP_ALIVE_URL", required=False)
    check_env_var("SECRET_KEY", required=False)
    print()
    
    # Check Python packages
    print("📦 Checking Python Packages:")
    packages = ["telethon", "requests", "flask", "flask_login", "dotenv"]
    for package in packages:
        try:
            __import__(package if package != "dotenv" else "dotenv")
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (Run: pip install -r requirements.txt)")
            all_good = False
    print()
    
    # Final verdict
    if all_good:
        print("🎉 All checks passed! You're ready to run the bot.")
        print("\n🚀 Next steps:")
        print("1. Run: python app.py")
        print("2. Visit: http://localhost:5000")
        print("3. Login with your credentials")
        print("4. Go to Settings → Add invitation codes")
        print("5. Start the bot!")
        print("\n📖 For deployment: See DEPLOYMENT.md")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n📝 Common fixes:")
        print("1. Copy .env.example to .env and fill in values")
        print("2. Run: pip install -r requirements.txt")
        print("3. Check DEPLOYMENT.md for detailed setup")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏸️ Setup verification cancelled.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
