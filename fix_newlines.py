for filename in ['src/scanners/run_options_intraday_scan_powerful_sl.py', 'src/scanners/run_btst_options_scan_powerful_sl.py']:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('print(f"\n📰 [NEWS INTEGRATION]', 'print(f"\n📰 [NEWS INTEGRATION]')
    content = content.replace('print("\n⚠️  [NEWS INTEGRATION]', 'print("\n⚠️  [NEWS INTEGRATION]')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
