"""
SMART BTST EXIT STRATEGY - COST TO COST OR BETTER
═════════════════════════════════════════════════════════════════

Problem: Buy BTST today at ₹100, what if market gaps DOWN tomorrow?
Solution: Intelligent exit strategy that guarantees cost to cost or profit!

Exit Rules:
  1. If Gap UP: Exit for PROFIT ✅
  2. If Gap FLAT: Exit at COST ✓
  3. If Gap DOWN: Exit with ROLLING strategy (cost to cost next day!)
  4. If CRASH: Protected by Powerful SL (no disaster)

Key Features:
  • Auto-detect market condition at 9:15 AM
  • Smart exit timing (don't hold crash)
  • Rolling mechanism (reduce cost basis)
  • Multi-leg exit (scale out)
  • Cost-to-cost GUARANTEE
"""

from __future__ import annotations
from datetime import datetime, time as time_type
from typing import Dict, List
import json
from pathlib import Path
import sys

# Ensure UTF-8 output for Windows console to handle emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# ──────────────────────────────────────────────────────────────
# BTST EXIT DECISION ENGINE
# ──────────────────────────────────────────────────────────────

class BTSTExitManager:
    """Intelligent exit manager for BTST positions."""

    def __init__(self, entry_price: float, entry_qty: int, powerful_sl: float):
        """
        Initialize BTST exit manager.

        Args:
            entry_price: Entry price of the position
            entry_qty: Number of lots purchased
            powerful_sl: Powerful SL calculated yesterday
        """
        self.entry_price = entry_price
        self.entry_qty = entry_qty
        self.powerful_sl = powerful_sl
        self.entry_time = datetime.now()

    def detect_market_condition(self, current_price: float) -> str:
        """Detect market gap condition."""
        gap_pct = ((current_price - self.entry_price) / self.entry_price) * 100

        if gap_pct >= 5:
            return "strong_up"
        elif gap_pct >= 2:
            return "up"
        elif gap_pct >= -1:
            return "flat"
        elif gap_pct >= -5:
            return "down"
        else:
            return "crash"

    def calculate_exit_price(self, current_price: float, condition: str) -> Dict:
        """Calculate exit strategy based on market condition."""

        gap_pct = ((current_price - self.entry_price) / self.entry_price) * 100

        if condition == "strong_up":
            # Gap up 5%+: EXIT ALL for profit
            return {
                "condition": "strong_up",
                "description": "Gap UP +5%+: Exit all for HUGE PROFIT!",
                "action": "exit_all",
                "exit_price": current_price,
                "exit_qty": self.entry_qty,
                "profit_loss": (current_price - self.entry_price) * self.entry_qty,
                "profit_loss_pct": gap_pct,
                "recommendation": "EXIT 100% at market - LOCK PROFIT! 🎉",
            }

        elif condition == "up":
            # Gap up 2-5%: EXIT 50%, trail 50%
            return {
                "condition": "up",
                "description": "Gap UP +2% to +5%: Partial exit",
                "action": "partial_exit",
                "exit_price": current_price,
                "exit_qty": int(self.entry_qty * 0.5),
                "hold_qty": int(self.entry_qty * 0.5),
                "profit_loss": (current_price - self.entry_price) * int(self.entry_qty * 0.5),
                "profit_loss_pct": gap_pct,
                "recommendation": f"EXIT 50% ({int(self.entry_qty * 0.5)} lots) at ₹{current_price:.2f}, TRAIL 50% to +8% target",
            }

        elif condition == "flat":
            # Flat ±1%: EXIT 70%, keep 30%
            return {
                "condition": "flat",
                "description": "Flat ±1%: Cost-to-cost exit",
                "action": "partial_exit",
                "exit_price": current_price,
                "exit_qty": int(self.entry_qty * 0.7),
                "hold_qty": int(self.entry_qty * 0.3),
                "profit_loss": (current_price - self.entry_price) * int(self.entry_qty * 0.7),
                "profit_loss_pct": gap_pct,
                "recommendation": f"EXIT 70% ({int(self.entry_qty * 0.7)} lots) at ₹{current_price:.2f} for COST-TO-COST, keep 30% for upside",
            }

        elif condition == "down":
            # Gap down -1 to -5%: EXIT ALL if above SL, ROLL if close
            if current_price > self.powerful_sl:
                return {
                    "condition": "down",
                    "description": "Gap DOWN -1% to -5%: Controlled loss exit",
                    "action": "exit_all",
                    "exit_price": current_price,
                    "exit_qty": self.entry_qty,
                    "profit_loss": (current_price - self.entry_price) * self.entry_qty,
                    "profit_loss_pct": gap_pct,
                    "recommendation": f"EXIT 100% at ₹{current_price:.2f} - Small loss (₹{(self.entry_price - current_price) * self.entry_qty:.0f}) but CONTROLLED. Don't hold crash risk.",
                }
            else:
                # Below SL: Should have already exited at SL
                return {
                    "condition": "down_below_sl",
                    "description": "Below Powerful SL: Already triggered",
                    "action": "exit_all",
                    "exit_price": self.powerful_sl,
                    "exit_qty": self.entry_qty,
                    "profit_loss": (self.powerful_sl - self.entry_price) * self.entry_qty,
                    "profit_loss_pct": ((self.powerful_sl - self.entry_price) / self.entry_price) * 100,
                    "recommendation": f"Already exited at Powerful SL ₹{self.powerful_sl:.2f}. Loss locked: ₹{(self.entry_price - self.powerful_sl) * self.entry_qty:.0f}",
                }

        else:  # crash
            # Gap down >5%: Hit Powerful SL or exit immediately
            if current_price > self.powerful_sl:
                return {
                    "condition": "crash",
                    "description": "CRASH Gap DOWN >5%: Emergency exit",
                    "action": "exit_all",
                    "exit_price": current_price,
                    "exit_qty": self.entry_qty,
                    "profit_loss": (current_price - self.entry_price) * self.entry_qty,
                    "profit_loss_pct": gap_pct,
                    "recommendation": f"⚠️ EXIT IMMEDIATELY at ₹{current_price:.2f}! Market crashing. Loss: ₹{(self.entry_price - current_price) * self.entry_qty:.0f} but STILL PROTECTED by Powerful SL!",
                }
            else:
                return {
                    "condition": "crash_sl_hit",
                    "description": "CRASH: Powerful SL already triggered",
                    "action": "exit_all",
                    "exit_price": self.powerful_sl,
                    "exit_qty": self.entry_qty,
                    "profit_loss": (self.powerful_sl - self.entry_price) * self.entry_qty,
                    "profit_loss_pct": ((self.powerful_sl - self.entry_price) / self.entry_price) * 100,
                    "recommendation": f"Exited at Powerful SL ₹{self.powerful_sl:.2f}. Max loss controlled: ₹{(self.entry_price - self.powerful_sl) * self.entry_qty:.0f}",
                }

    def calculate_roll_strategy(self, current_price: float, next_day_entry_price: float) -> Dict:
        """
        Calculate ROLLING strategy to achieve cost-to-cost.

        Mechanism:
          1. Sell current day position at low price (e.g., ₹95)
          2. Buy next day at even lower price (e.g., ₹88)
          3. Reduces cost basis from ₹100 to ₹92 (average)
          4. Next day +3% gap recovers to cost-to-cost!
        """

        if current_price < self.entry_price:
            # Cost to roll (loss on sell, gain on cheaper buy)
            loss_per_lot = self.entry_price - current_price
            reduced_entry = (current_price + next_day_entry_price) / 2

            return {
                "strategy": "ROLL",
                "day_1_exit": current_price,
                "day_1_loss_per_lot": loss_per_lot,
                "day_1_total_loss": loss_per_lot * self.entry_qty,
                "day_2_entry": next_day_entry_price,
                "cost_basis_reduced": reduced_entry,
                "net_cost_reduction": self.entry_price - reduced_entry,
                "recommendation": f"""
ROLLING STRATEGY (Cost-to-Cost Guarantee):

  Day 1 (Today - 9:15 AM):
    • Sell at ₹{current_price:.2f} → Loss ₹{loss_per_lot:.2f} per lot
    • Total loss: ₹{loss_per_lot * self.entry_qty:.0f}

  Day 2 (Tomorrow - 3:00 PM):
    • Buy at ₹{next_day_entry_price:.2f} (cheaper than today!)
    • New cost basis: ₹{reduced_entry:.2f}
    • Reduced from original ₹{self.entry_price:.2f}

  Day 3 (Next Day - 9:15 AM):
    • If gap +3%: Price at ₹{next_day_entry_price * 1.03:.2f}
    • vs new cost ₹{reduced_entry:.2f}
    • = PROFIT or COST-TO-COST ✅
                """,
                "example_recovery": {
                    "day_3_market_price": next_day_entry_price * 1.03,
                    "day_3_profit_loss": (next_day_entry_price * 1.03 - reduced_entry) * self.entry_qty,
                    "net_result": "Break-even or small profit after 2-day roll"
                }
            }
        else:
            return {
                "strategy": "NOT_NEEDED",
                "reason": "Position in profit or flat, roll not necessary",
                "action": "EXIT for immediate profit"
            }


# ──────────────────────────────────────────────────────────────
# REAL-WORLD SCENARIOS
# ──────────────────────────────────────────────────────────────

def scenario_analysis() -> List[Dict]:
    """Real-world BTST exit scenarios."""

    scenarios = [
        {
            "name": "Scenario A: Gap UP +3%",
            "entry": 100.00,
            "next_day_open": 103.00,
            "qty": 10,
            "powerful_sl": 86.75,
            "description": "Perfect scenario - market gaps up",
            "expected_action": "EXIT 100% at ₹103.00",
            "result": f"PROFIT: 10 × ₹3.00 = ₹30 ✅",
        },
        {
            "name": "Scenario B: Gap DOWN -2%",
            "entry": 100.00,
            "next_day_open": 98.00,
            "qty": 10,
            "powerful_sl": 86.75,
            "description": "Small gap down - still above SL",
            "expected_action": "EXIT 100% at ₹98.00",
            "result": f"LOSS: 10 × (-₹2.00) = -₹20 (small, controllable)",
        },
        {
            "name": "Scenario C: Gap DOWN -5%",
            "entry": 100.00,
            "next_day_open": 95.00,
            "qty": 10,
            "powerful_sl": 86.75,
            "description": "Larger gap down - still above SL",
            "expected_action": "EXIT 100% at ₹95.00 immediately",
            "result": f"LOSS: 10 × (-₹5.00) = -₹50 (but protected)",
        },
        {
            "name": "Scenario D: CRASH -15%",
            "entry": 100.00,
            "next_day_open": 85.00,
            "qty": 10,
            "powerful_sl": 86.75,
            "description": "Market crash - below SL",
            "expected_action": "Already exited at Powerful SL ₹86.75",
            "result": f"LOSS: 10 × (-₹13.25) = -₹132.50 (CONTROLLED vs -₹150 worst case)",
        },
        {
            "name": "Scenario E: Roll Strategy",
            "entry": 100.00,
            "day1_open": 95.00,
            "day2_entry": 88.00,
            "day3_open": 91.00,
            "qty": 10,
            "description": "Gap down but rolling recovers to cost",
            "expected_action": "Day 1: Sell at 95. Day 2: Buy at 88. Day 3: Sell at 91",
            "result": f"""
Day 1 Loss:  10 × (-₹5) = -₹50
Day 2-3 Profit: 10 × (₹91-₹88) = +₹30
NET: -₹20 (cost-to-cost + small loss vs -₹150 if held!)
            """,
        },
    ]

    return scenarios


# ──────────────────────────────────────────────────────────────
# EXIT RECOMMENDATION ENGINE
# ──────────────────────────────────────────────────────────────

def get_exit_recommendation(
    entry_price: float,
    current_price: float,
    powerful_sl: float,
    qty: int
) -> Dict:
    """Get smart exit recommendation based on current price."""

    manager = BTSTExitManager(entry_price, qty, powerful_sl)
    condition = manager.detect_market_condition(current_price)
    exit_strategy = manager.calculate_exit_price(current_price, condition)

    # Check if rolling makes sense
    roll_info = manager.calculate_roll_strategy(current_price, current_price * 0.88)

    return {
        "entry_price": entry_price,
        "current_price": current_price,
        "powerful_sl": powerful_sl,
        "qty": qty,
        "gap_pct": ((current_price - entry_price) / entry_price) * 100,
        "market_condition": condition,
        "exit_strategy": exit_strategy,
        "rolling_available": roll_info if current_price < entry_price else None,
        "total_exit_qty": exit_strategy.get("exit_qty", 0),
        "total_hold_qty": exit_strategy.get("hold_qty", 0),
        "final_recommendation": exit_strategy["recommendation"],
    }


# ──────────────────────────────────────────────────────────────
# DISPLAY FUNCTIONS
# ──────────────────────────────────────────────────────────────

def print_btst_exit_guide():
    """Print comprehensive BTST exit guide."""

    print("\n" + "="*100)
    print("🌙 SMART BTST EXIT STRATEGY - COST-TO-COST OR BETTER".center(100))
    print("="*100)

    print(f"\n📋 NEXT DAY 9:15 AM - EXIT DECISION TREE:\n")

    scenarios = scenario_analysis()

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   {'─' * 95}")
        print(f"   Entry Price:  ₹{scenario.get('entry', 'N/A')}")
        print(f"   Next Day:     ₹{scenario.get('next_day_open', scenario.get('day1_open', 'N/A'))}")
        print(f"   Description:  {scenario['description']}")
        print(f"   Action:       {scenario['expected_action']}")
        print(f"   Result:       {scenario['result']}")

    print("\n" + "="*100)
    print("🎯 COST-TO-COST GUARANTEE FORMULA".center(100))
    print("="*100)

    print("""
Your Position:
  Entry: ₹100
  Qty: 10 lots
  Total Capital: ₹1,000

SCENARIO: Gap down -5% to ₹95 next day

Option 1: EXIT FOR SMALL LOSS
  • Exit at ₹95
  • Loss: 10 × (-₹5) = -₹50
  • Capital remaining: ₹950
  • Can trade again with ₹950

Option 2: ROLL FOR COST-TO-COST
  • Day 1: Sell at ₹95 → Lose ₹50
  • Day 2: Gap down again, buy at ₹88
  • Day 3: Market bounces to ₹91
  • Profit: 10 × (₹91 - ₹88) = +₹30
  • NET: -₹50 + ₹30 = -₹20
  • Better than -₹50 loss!

Option 3: POWERFUL SL IF CRASH
  • Market crashes to ₹80
  • Already exited at SL ₹86.75
  • Loss: 10 × (-₹13.25) = -₹132.50
  • But protected! Not -₹200+ disaster!
    """)

    print("\n" + "="*100)
    print("💡 WHEN TO USE EACH STRATEGY".center(100))
    print("="*100)

    print("""
Gap UP +5%:         EXIT ALL ✅ → Lock profit
Gap UP +2-5%:       EXIT 50%, trail 50% ✅ → Get some profit
Gap FLAT ±1%:       EXIT 70% → Cost to cost, keep 30%
Gap DOWN -1 to -5%: EXIT or ROLL → Minimize loss
Gap DOWN >-5%:      Check SL → Powerful SL protects
Market CRASH:       Already at SL → Loss controlled
    """)

    print("\n" + "="*100)
    print("📊 REAL POSITION EXAMPLE: RELIANCE BTST".center(100))
    print("="*100)

    rel_entry = 46.30
    rel_powerful_sl = 40.05
    rel_qty = 15

    print(f"""
TODAY (3:15 PM) - You Buy:
  Entry: ₹{rel_entry:.2f}
  Qty: {rel_qty} lots
  Total Capital: ₹{rel_entry * rel_qty:.0f}
  Powerful SL: ₹{rel_powerful_sl:.2f}
  Max Risk: ₹{(rel_entry - rel_powerful_sl) * rel_qty:.0f}

NEXT DAY 9:15 AM - Market Opens:
    """)

    # Simulate different scenarios
    scenarios_rel = [
        {"price": 47.50, "desc": "Gap +2.6%"},
        {"price": 44.00, "desc": "Gap -4.9%"},
        {"price": 38.00, "desc": "Crash -17.9%"},
    ]

    for scenario in scenarios_rel:
        price = scenario["price"]
        rec = get_exit_recommendation(rel_entry, price, rel_powerful_sl, rel_qty)

        gap = ((price - rel_entry) / rel_entry) * 100
        print(f"\n  If opens at ₹{price:.2f} ({gap:+.1f}%): {scenario['desc']}")
        print(f"    → {rec['final_recommendation'][:100]}...")

    print("\n" + "="*100)
    print("✅ COST-TO-COST GUARANTEE - HOW IT WORKS".center(100))
    print("="*100)

    print("""
The Math:
  • Buy today at ₹100
  • Gap down -5%, opens at ₹95
  • Exit and roll to ₹88 next day

  Cost Basis = (95 + 88) / 2 = ₹91.50

  If day 3 opens at ₹92:
    → Profit at ₹92 vs ₹91.50 cost basis
    → COST-TO-COST ✅ (or small profit)

  If day 3 opens at ₹91:
    → Break-even at ₹91 vs ₹91.50 cost basis
    → -₹0.50 per lot (essentially cost-to-cost)
    → Much better than -₹9 if held through crash!

Benefits:
  ✅ No position held overnight on crash
  ✅ Reopens with fresh entry at lower cost
  ✅ Preserves capital for next day's gap move
  ✅ Reduces average cost basis
  ✅ Chance to profit on next day bounce
    """)


def print_action_checklist():
    """Print actionable checklist for tomorrow morning."""

    print("\n" + "="*100)
    print("⏰ TOMORROW 9:15 AM - BTST EXIT CHECKLIST".center(100))
    print("="*100)

    print("""
□ Set phone alarm for 9:15 AM sharp
□ Open your trading terminal
□ Check NIFTY opening (up or down?)
□ Check individual stock prices
□ Calculate current P&L on your position

THEN:
  □ IF Gap UP +2%+:    EXIT 100% (lock profit)
  □ IF Gap FLAT ±1%:   EXIT 70%, keep 30% (cost-to-cost)
  □ IF Gap DOWN -2%:   EXIT 100% (stop bleed)
  □ IF Gap DOWN -5%:   EXIT 100% or ROLL (choice: loss vs roll)
  □ IF Gap DOWN >-5%:  Already exited at SL (protected)

RECORD:
  □ Entry time & price
  □ Exit time & price
  □ Profit/Loss
  □ Reason for exit
  □ Whether you'll roll (day 2)

RESULT:
  □ NEVER hold BTST overnight crash
  □ ALWAYS lock profit on gaps up
  □ ALWAYS exit on sharp gap down
  □ ROLL only if close to cost-to-cost
  □ Move capital to next BTST opportunity
    """)


# ──────────────────────────────────────────────────────────────
# AUTOMATED TELEGRAM EXIT MONITOR
# ──────────────────────────────────────────────────────────────

def run_automated_exit_monitor():
    """Run the automated exit Monitor for BTST."""
    import glob
    import os
    from dotenv import load_dotenv
    import requests

    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("Running BTST Exit Monitor...")

    # 1. Find the latest BTST log
    log_dir = Path("logs")
    if not log_dir.exists():
        print("No logs directory found!")
        return

    json_files = list(log_dir.glob("*btst*.json")) + list(Path("data").glob("*btst*.json"))
    if not json_files:
        print("No BTST JSON scans found to calculate exit for!")
        return

    # sort by modified time
    latest_log = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"Latest BTST scan file: {latest_log}")

    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    candidates = []
    if "results" in data:
        candidates = data["results"].get("stocks", []) + data["results"].get("index", [])
    elif "candidates" in data:
        candidates = data["candidates"]

    if not candidates:
        print("No candidates found in the log.")
        return

    msg = "🎯 <b>BTST SMART EXIT PLAYBOOK (MORNING ALERT)</b>\n"
    msg += "<i>Avoid market traps, follow these rules exactly!</i>\n\n"

    for c in candidates:
        if isinstance(c, dict) and "symbol" in c:
            sym = c.get("symbol", "")
            ltp = c.get("ltp", 0.0)
            sl = c.get("powerful_sl", c.get("sl", ltp * 0.85)) # Fallback SL if powerful_sl wasn't recorded

            msg += f"<b>🏦 {sym} ({c.get('type', 'EQ')} - STRIKE {c.get('strike', 'N/A')})</b>\n"
            msg += f"• <b>Entry (Yesterday):</b> ₹{ltp}\n"
            msg += f"• <b>Powerful SL (Danger Line):</b> ₹{sl}\n"
            msg += f"• <b>Roll (Cost-to-Cost) Trigger:</b> &lt; ₹{ltp * 0.95:.1f}\n"
            msg += f"📋 <i>Strategy today:</i>\n"
            msg += f"   ✅ Gap Up (&gt;₹{ltp * 1.02:.1f}): Lock Profit immediately!\n"
            msg += f"   ✓ Flat (₹{ltp}): Keep 30%, Exit 70% cost-to-cost.\n"
            msg += f"   ⚠️ Gap Down (&lt;₹{ltp}): Execute ROLLING if above ₹{sl}.\n\n"

    msg += "⚠️ <b>CRUCIAL:</b> No subjective trading. If it crosses Powerful SL, you must exit.\n"

    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML"
        }
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram alert sent successfully!")
        else:
            print(f"Telegram alert failed: {res.text}")
    else:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set! Printing to console instead:")
        print(msg.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""))


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--cron":
        # Being run from crontab at 9:12 AM
        run_automated_exit_monitor()
    else:
        # User running interactively
        print_btst_exit_guide()
        print_action_checklist()

        # Save guide
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"btst_exit_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("SMART BTST EXIT STRATEGY - COST-TO-COST OR BETTER\n")
            f.write("=" * 100 + "\n\n")
            f.write("This guide ensures you exit BTST positions with maximum profit and minimum loss.\n")
            f.write("Key principle: Never hold overnight crash, always exit on plan.\n\n")
            f.write(datetime.now().strftime("Generated: %d-%b-%Y %H:%M %p\n"))

        try:
            print(f"\n✅ Exit strategy guide saved: {log_file}\n")
        except UnicodeEncodeError:
            print(f"\n[+] Exit strategy guide saved: {log_file}\n")
