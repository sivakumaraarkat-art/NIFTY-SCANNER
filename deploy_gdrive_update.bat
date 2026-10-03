@echo off
echo Compressing updated script...
tar.exe --exclude=".venv" --exclude=".trash" --exclude="__pycache__" --exclude=".git" --exclude="*.key" -czf update.tar.gz src/scanners/generate_weekly_audit.py .env.example
echo.
echo Uploading to VM...
scp -i "D:\NiftyScanner\oracle\nifty-v15.key" -o StrictHostKeyChecking=no update.tar.gz ubuntu@140.245.195.112:/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/
echo.
echo Extracting on VM...
ssh -i "D:\NiftyScanner\oracle\nifty-v15.key" ubuntu@140.245.195.112 "cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && tar -xzf update.tar.gz && rm update.tar.gz"
echo.
echo Done!
del update.tar.gz
