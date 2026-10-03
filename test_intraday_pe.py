import sys
from importlib import import_module
from unittest.mock import patch

with patch('src.scanners.run_options_intraday_scan_powerful_sl.is_trading_day', return_value=True):
    # Set fake args to trigger news candidate feature
    sys.argv = ['run_options_intraday_scan_powerful_sl.py', '--use-news-candidates']
    # Load and run script
    mod = import_module('src.scanners.run_options_intraday_scan_powerful_sl')
    mod.main()
