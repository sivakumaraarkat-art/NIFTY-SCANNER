from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_cell_shading(cell, fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:fill'), fill)
    shd.set(qn('w:val'), 'clear')


examples = [
    {
        'rank': 1,
        'name': 'NIFTY 500 Top Gainers Intraday Basket',
        'scenario': 'Tata Motors is among the strongest gainers in the NIFTY 500 basket. The market opens with broad strength and the stock remains above its opening range.',
        'entry': 'Buy Tata Motors as part of a basket when it is in the top gainers list and remains above the opening range high.',
        'stop': 'Place stop below the opening range low or a fixed risk of 1.5% from entry.',
        'target': 'Target 2% to 3% or close the basket when the gainers list weakens.',
        'why': 'This works because strong momentum breadth increases the chance that leaders continue moving.'
    },
    {
        'rank': 2,
        'name': 'Intraday Breakout Momentum Basket',
        'scenario': 'Tata Motors trades in a tight ₹960–₹975 range and then breaks above ₹980 with heavier volume.',
        'entry': 'Buy on the breakout candle after the close is above ₹980 and the volume is above the recent average.',
        'stop': 'Stop below ₹972 or the recent range low.',
        'target': 'Target around ₹995–₹1,000.',
        'why': 'Breakout traders aim to catch the fastest part of the move when participation is strong.'
    },
    {
        'rank': 3,
        'name': 'Opening Range Breakout',
        'scenario': 'Tata Motors opens at ₹970, trades within ₹968–₹978, and then breaks above ₹978.80.',
        'entry': 'Buy when price breaks and holds above the opening range high.',
        'stop': 'Stop below the opening range low, near ₹972.',
        'target': 'Target ₹990 or the next resistance.',
        'why': 'First-hour breakout trades often work when the stock continues its directional move.'
    },
    {
        'rank': 4,
        'name': 'VWAP Reclaim / Trend Resumption',
        'scenario': 'Tata Motors rallies but briefly slips toward VWAP before reclaiming it with strength.',
        'entry': 'Buy after price closes back above VWAP and momentum stays positive.',
        'stop': 'Place stop below VWAP support.',
        'target': 'Target the recent swing high or the next strong resistance.',
        'why': 'VWAP reclaim often signals the continuation of a healthy trend.'
    },
    {
        'rank': 5,
        'name': 'Relative Strength Leaders',
        'scenario': 'The market is strong and Tata Motors is outperforming both the NIFTY and peers.',
        'entry': 'Buy when Tata Motors is ranked among the strongest stocks in the sector or broader market.',
        'stop': 'Use a stop below the short-term trend support.',
        'target': 'Target the next strong resistance or a 2%–3% move.',
        'why': 'Relative strength helps filter the best names when many stocks are moving.'
    },
    {
        'rank': 6,
        'name': 'Pullback Continuation',
        'scenario': 'Tata Motors rises from ₹960 to ₹995 and then pulls back to ₹985 before bouncing upward.',
        'entry': 'Buy near support after a higher low and positive price action.',
        'stop': 'Stop below the pullback low, near ₹981.',
        'target': 'Target the prior swing high or ₹1,005.',
        'why': 'This trade attempts to participate in the trend without buying at the top.'
    },
    {
        'rank': 7,
        'name': 'Gap-Up Continuation',
        'scenario': 'Tata Motors opens sharply higher at ₹990 and remains strong after the first 15 minutes.',
        'entry': 'Buy near the opening price or after confirming the gap-up holds above the opening level.',
        'stop': 'Stop below the first-hour low or the gap zone.',
        'target': 'Target around ₹1,010.',
        'why': 'Gap-ups work when momentum remains strong and buyers continue to defend the move.'
    },
    {
        'rank': 8,
        'name': 'Sector Momentum Rotation',
        'scenario': 'Auto stocks outperform the market, and Tata Motors is one of the strongest names in that sector.',
        'entry': 'Buy Tata Motors when auto-sector leadership is strong and multiple peers are also rising.',
        'stop': 'Use the sector trend or a stop below the short-term structure.',
        'target': 'Move toward the next sector leader level or a defined profit zone.',
        'why': 'Sector leadership helps align a single stock trade with the market environment.'
    },
    {
        'rank': 9,
        'name': 'High-Volume Breakout',
        'scenario': 'Tata Motors breaks above resistance with volume much above its average.',
        'entry': 'Buy only if the close is strong and participation remains elevated.',
        'stop': 'Stop below the breakout zone.',
        'target': 'Target the next resistance or a 2% move.',
        'why': 'A high-volume breakout is usually a stronger and cleaner signal than a low-volume move.'
    },
    {
        'rank': 10,
        'name': 'Reversal from Support',
        'scenario': 'Tata Motors pulls back to a key support level but forms a bullish reversal candle.',
        'entry': 'Buy near support after a bullish candle or a higher low appears.',
        'stop': 'Stop below the support zone.',
        'target': 'Target the recent swing high or the next resistance.',
        'why': 'The trade tries to capture a bounce from a healthy support base.'
    },
    {
        'rank': 11,
        'name': 'Bullish Engulfing Trend Continuation',
        'scenario': 'After a minor pullback, Tata Motors forms a large green candle that engulfs the previous red candle.',
        'entry': 'Buy when the engulfing candle closes above the recent consolidation.',
        'stop': 'Stop under the recent swing low.',
        'target': 'Target the next minor high or the trend continuation level.',
        'why': 'This pattern is often seen in trend continuation after a brief pause.'
    },
    {
        'rank': 12,
        'name': 'Oversold Rebound Basket',
        'scenario': 'Tata Motors has a sharp morning selloff but then starts creating higher lows and stabilizes.',
        'entry': 'Buy after oversold conditions improve and the stock starts recovering.',
        'stop': 'Use a tight stop just below the short-term support zone.',
        'target': 'Target the first strong resistance layer.',
        'why': 'Oversold rebounds can work well in short bursts when pressure is fading.'
    },
    {
        'rank': 13,
        'name': 'Morning Momentum Spike',
        'scenario': 'Tata Motors spikes higher between 09:15 and 10:30 with strong volume.',
        'entry': 'Buy on the morning move while momentum remains positive and price stays above the opening thrust.',
        'stop': 'Place stop below the first-hour base.',
        'target': 'Target the early-morning range high or a fixed profit zone.',
        'why': 'This is a fast-moving setup when volatility is strongest.'
    },
    {
        'rank': 14,
        'name': 'Trend-Following Pullback',
        'scenario': 'The stock is in a clear uptrend but briefly dips to a trend support zone.',
        'entry': 'Buy on the bounce when the trend remains intact and support holds.',
        'stop': 'Stop below the trend support zone.',
        'target': 'Target the last higher high or continuation level.',
        'why': 'Trend-following pullbacks often provide better entry quality than chasing the top of the move.'
    },
    {
        'rank': 15,
        'name': 'Low-Risk Breakout with Filter',
        'scenario': 'Tata Motors breaks above resistance, but only after confirming market health, volume, and price structure.',
        'entry': 'Buy only if the breakout is clean, the overall market is supportive, and volume is above threshold.',
        'stop': 'Stop below the confirmed breakout zone.',
        'target': 'Target the next resistance or a calculated move that matches risk.',
        'why': 'Quality filters reduce poor breakouts and make the system more disciplined.'
    },
]


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.5)
section.bottom_margin = Inches(0.5)
section.left_margin = Inches(0.55)
section.right_margin = Inches(0.55)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('FYERS Automation Example: Tata Motors')
run.bold = True
run.font.size = Pt(24)

intro = doc.add_paragraph()
intro.add_run('This document shows how the same stock can behave under all automation styles. The example stock is Tata Motors, with a sample entry, stop, and target for each strategy setup.')

summary = doc.add_table(rows=1, cols=4)
summary.style = 'Table Grid'
header = summary.rows[0].cells
header[0].text = 'Rank'
header[1].text = 'Automation'
header[2].text = 'Sample Entry'
header[3].text = 'Risk / Target'
for item in examples:
    row = summary.add_row().cells
    row[0].text = str(item['rank'])
    row[1].text = item['name']
    row[2].text = item['entry']
    row[3].text = f"Stop: {item['stop']} | Target: {item['target']}"
    for cell in row:
        set_cell_shading(cell, 'D9EAF7' if item['rank'] % 2 == 1 else 'EAF7D9')

for item in examples:
    doc.add_paragraph()
    h = doc.add_heading(f"{item['rank']}. {item['name']}", level=1)
    h.runs[0].font.size = Pt(16)
    doc.add_paragraph('Scenario: ' + item['scenario'])
    doc.add_paragraph('Entry: ' + item['entry'])
    doc.add_paragraph('Stop: ' + item['stop'])
    doc.add_paragraph('Target: ' + item['target'])
    doc.add_paragraph('Why it works: ' + item['why'])

note = doc.add_paragraph()
note.add_run('Final interpretation: Tata Motors is a good example stock because it can fit breakout, pullback, continuation, gap-up, and basket-style automation rules. The exact trade quality depends on volume, market breadth, and whether risk is managed properly.')

out_path = 'FYERS_Automation_Examples_Updated.docx'
doc.save(out_path)
print(f'Created beautiful stock-based Word document: {out_path}')
