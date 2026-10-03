@echo off
echo Adding Weekly Audit to VM Schedule...
ssh -i "D:\NiftyScanner\oracle\nifty-v15.key" ubuntu@140.245.195.112 "(crontab -l 2>/dev/null; echo '35 15 * * 5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && python3 src/scanners/generate_weekly_audit.py >> logs/cron_audit.log 2>&1') | crontab -"
echo Schedule Updated Successfully!
pause
