# Temporary wrapper to disable trading day check and run intraday
import sys
from unittest.mock import patch
from src.scanners.run_options_intraday_scan_powerful_sl import main

with patch("src.scanners.run_options_intraday_scan_powerful_sl.is_trading_day", return_value=True):
    sys.argv = ["prog", "--use-news-candidates"]
    main()
