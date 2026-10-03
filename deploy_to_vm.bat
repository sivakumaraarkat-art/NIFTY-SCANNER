@echo off
echo Compressing project files...
tar.exe --exclude=".venv-1" --exclude=".trash" --exclude="__pycache__" --exclude=".git" --exclude="*.key" -czf nifty_update.tar.gz .
echo.
echo Uploading to VM...
scp -i "D:\NiftyScanner\oracle\nifty-v15.key" -o StrictHostKeyChecking=no nifty_update.tar.gz ubuntu@140.245.195.112:/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/
echo.
echo Extracting on VM...
ssh -i "D:\NiftyScanner\oracle\nifty-v15.key" ubuntu@140.245.195.112 "mkdir -p /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && tar -xzf nifty_update.tar.gz && rm nifty_update.tar.gz"
echo.
echo Done! Deployment to VM successful.
del nifty_update.tar.gz
del nifty_update_safe.tar.gz
