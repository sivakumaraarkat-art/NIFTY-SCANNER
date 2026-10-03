@echo off
echo Updating crontab on VM with the new BTST Exit Monitor...
ssh -i "D:\NiftyScanner\oracle\nifty-v15.key" -o StrictHostKeyChecking=no ubuntu@140.245.195.112 "crontab -l > /tmp/cron_bak && echo '12 09 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/run_btst_exit_monitor.py >> logs/cron_btst_exit.log 2>&1' >> /tmp/cron_bak && crontab /tmp/cron_bak"
echo Done! Crontab successfully updated.
pause
