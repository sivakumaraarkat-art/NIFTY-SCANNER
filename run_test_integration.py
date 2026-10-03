import sys
from unittest.mock import patch
from src.scanners.run_options_intraday_scan_powerful_sl import main

print("Forcing is_trading_day=True to test News JSON -> Intraday Scanner link...")
with patch("src.scanners.run_options_intraday_scan_powerful_sl.is_trading_day", return_value=True):
    sys.argv = ["dummy", "--use-news-candidates"]
    main()
