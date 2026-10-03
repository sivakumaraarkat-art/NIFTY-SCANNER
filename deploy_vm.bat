@echo off
echo [1/4] Compressing local project safely...
tar.exe --exclude=".venv*" --exclude=".trash" --exclude="__pycache__" --exclude=".git" --exclude="*.key" --exclude=".env" -czf update.tar.gz .
echo.

echo [2/4] Uploading to VM...
scp -i "D:\NiftyScanner\oracle\nifty-v15.key" -o StrictHostKeyChecking=no update.tar.gz ubuntu@140.245.195.112:/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/
echo.

echo [3/4] Extracting on VM...
ssh -i "D:\NiftyScanner\oracle\nifty-v15.key" ubuntu@140.245.195.112 "cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && tar -xzf update.tar.gz && rm update.tar.gz"
echo.

echo [4/4] Cleaning up local temporary files...
del update.tar.gz
echo.

echo ==============================================
echo  SUCCESS: VM is now fully synced with local!
echo ==============================================
pause
