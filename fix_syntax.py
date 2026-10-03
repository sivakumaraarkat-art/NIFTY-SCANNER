import re
for filename in ['src/scanners/run_options_intraday_scan_powerful_sl.py', 'src/scanners/run_btst_options_scan_powerful_sl.py']:
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out_lines = []
    for line in lines:
        if '📰 [NEWS INTEGRATION] Dynamic fetch complete from latest morning scan!")' in line and 'print' not in line:
            continue
        if '⚠️  [NEWS INTEGRATION] No recent news' in line and 'print' not in line:
            # Need to handle previous line being just print("
            pass
        out_lines.append(line)

    content = "".join(out_lines)
    
    # Clean the multi-line print statements
    content = re.sub(r'print\(f"\n📰 \[NEWS INTEGRATION\] Dynamic fetch complete from latest morning scan!"\)', 'print(f"\\n📰 [NEWS INTEGRATION] Dynamic fetch complete from latest morning scan!")', content)
    content = re.sub(r'print\("\n⚠️  \[NEWS INTEGRATION\] No recent news symbols found\. Falling back to default\."\)', 'print("\\n⚠️  [NEWS INTEGRATION] No recent news symbols found. Falling back to default.")', content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
