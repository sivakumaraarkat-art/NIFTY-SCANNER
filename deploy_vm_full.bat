@echo off
echo Compressing all local project updates safely...
tar.exe --exclude=".venv*" --exclude=".trash" --exclude="__pycache__" --exclude=".git" --exclude="*.key" --exclude=".env" -czf nifty_update_safe.tar.gz .
echo.
echo Uploading update to VM...
scp -i "D:\NiftyScanner\oracle\nifty-v15.key" -o StrictHostKeyChecking=no nifty_update_safe.tar.gz ubuntu@140.245.195.112:/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/
echo.
echo Extracting safely on VM (overwriting updated files)...
ssh -i "D:\NiftyScanner\oracle\nifty-v15.key" ubuntu@140.245.195.112 "cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && tar -xzf nifty_update_safe.tar.gz && rm nifty_update_safe.tar.gz"
echo.
echo Done! The VM is now 100%% synced with your local changes!
del nifty_update_safe.tar.gz
