
import sys
import os
import subprocess
from pathlib import Path

def install_deps():
    """Install required dependencies"""
    try:
        print("Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "customtkinter", "zstandard", "--user"
        ])
        print("Dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        return False

def main():
    """Main installer function"""
    print("ZSTD Decryptor Pro Installer")
    print("=" * 40)
    
    # Install dependencies
    if install_deps():
        # Run the main application
        try:
            from main import GZDecryptorApp
            app = GZDecryptorApp()
            app.mainloop()
        except ImportError as e:
            print(f"Failed to import main application: {e}")
            input("Press Enter to exit...")
    else:
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
