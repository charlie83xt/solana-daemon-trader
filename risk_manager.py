import csv
import os
from datetime import datetime, timedelta
from log_router import LogRouter

class RiskManager:
    def __init__(self, max_daily_loss=3.0, cooldown_minutes=10, log_file="logs/trade_log.csv"):
        self.max_daily_loss = max_daily_loss
        self.cooldown_minutes = cooldown_minutes
        self.log_file = log_file
        self.logger = LogRouter(use_drive=True)

        self._ensure_log_file()
        self.last_trade_time = None


    def _ensure_log_file(self):
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "action", "amount", "price", "confidence", "symbol", "tx_sig"])


    def log_trade(self, action, amount, price, confidence, symbol='SOL', tx_sig='-'):
        now = datetime.utcnow().isoformat()
        row = [now, action, amount, price, confidence]

        # For PnL: store BUYs and SELLs in matched pairs
        if action == 'BUY':
            row += ["", ""] # PnL and %return will be filled in after SELL
        elif action == 'SELL':
            pnl, ret = self.calculate_trade_pnl(amount, price)
            row += [round(pnl, 4), round(ret, 4)]
        else:
            row += ["", ""]

        with open(self.log_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([now, action, amount, price, confidence, symbol, tx_sig])
            try:
                self.logger.log_local_and_remote(self.log_file)
            except Exception as e:
                print(f"[DriveLogger] in RiskManager Failed to sync: {e}")
        self.last_trade_time = datetime.utcnow()


    def calculate_trade_pnl(self, sell_amount, sell_price):
        try:
            with open(self.log_file, mode='r') as f:
                rows = list(csv.reader(f))
                for row in reversed(rows[1:]): # skip header
                    if row[1] == 'BUY' and not row[-2]: # match unpaired BUY
                        buy_amount = float(row[2])
                        buy_price = float(row[3])
                        if abs(buy_amount - sell_amount) < 1e-6:
                            pnl = (sell_price - buy_price) * sell_amount
                            ret = (sell_price - buy_price) / buy_price
                            return pnl, ret
        except Exception as e:
            print(f"[RiskManager] Error calculating trade PnL: {e}")
        return 0.0, 0.0

    def print_summary(self):
        trades = 0
        wins = 0
        losses = 0
        total_pnl = 0

        try:
            with open(self.log_file, mode='r') as f:
                next(f)
                for row in csv.reader(f):
                    pnl = row[-2]
                    if pnl:
                        pnl = float(pnl)
                        trades += 1
                        total_pnl += pnl
                        if pnl > 0:
                            wins += 1
                        else:
                            losses += 1
            print(f"\n[Trade Summary]")
            print(f"    Total Trades: {trades}")
            print(f"    Wins: {wins}, Losses: {losses}")
            print(f"    Win Rate: {(wins / trades * 100):.2f}%" if trades else "    N/A")
            print(f"    Total PnL: {total_pnl:.4f} SOL")
        except Exception as e:
            print(f" [RiskManager] Summary error: {e}")



    def is_cooldown_active(self):
        if self.last_trade_time is None:
            return False
        return datetime.utcnow() < self.last_trade_time + timedelta(minutes=self.cooldown_minutes)


    def calculate_daily_loss(self):
        loss = 0.0
        today = datetime.utcnow().date
        try:
            with open(self.log_file, mode='r') as f:
                next(f) # Skipping header
                for row in csv.reader(f):
                    timestamp = datetime.fromisoformat(row[0])
                    action = row[1]
                    amount = float(row[2])
                    price = float(row[3])
                    
                    if timestamp.date() == today:
                        # Treat BUY as cost, SELL as profit (for now)
                        if action == 'BUY':
                            loss += amount * price
                        elif action == 'SELL':
                            loss -= amount * price
        except Exception as e:
            print(f"[RiskManager] Error calculating loss: {e}")
        return loss


    def approve_trade(self, decision, indicators):
        if self.is_cooldown_active():
            print(f"[RiskManager] Trade rejected due to cooldown.")
            return False

        daily_loss = self.calculate_daily_loss()
        if daily_loss > self.max_daily_loss:
            print(f"[RiskManager] Trade rejected due to max daily loss ({daily_loss:.2f} > {self.max_daily_loss})")
            return False

        if float(decision.get("confidence", 1.0)) < 0.6:
            print(f"[RiskManager] Trade rejected due to low confidence ({decision.get('confidence')})")
            return False

        return True

         
