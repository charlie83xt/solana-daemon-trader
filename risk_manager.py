import csv
import os
from datetime import datetime, timedelta
# from log_router import LogRouter
# from gdrive_logger import DriveLogger
import io
# from log_paths import TRADE_LOG
from db_logger import log_trade, fetch_all_trades


class RiskManager:
    def __init__(self, cooldown_minutes=10, log_file=None):
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 0.3))
        self.cooldown_minutes = cooldown_minutes
        # self.log_file = log_file or TRADE_LOG
        # self.logger = LogRouter(use_drive=True)
        self.max_position_size = float(os.getenv("MAX_POSITION", 0.05)) 

        # self._ensure_log_file()
        self.last_trade_time = None

        self.min_confidence = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", 0.75))
        self.max_loss_streak = int(os.getenv("MAX_CONSECUTIVE_LOSSES", 3))
        self.loss_streak = 0

    # def _ensure_log_file(self):
    #     os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    #     if not os.path.exists(self.log_file):
    #         with open(self.log_file, mode='w', newline='') as f:
    #             writer = csv.writer(f)
    #             writer.writerow(["timestamp", "action", "amount", "price", "confidence", "symbol", "tx_sig", "pnl", "return_pct", "sentiment"])


    def log_trade(self, action, amount, price, confidence, symbol='SOL', tx_sig='-', sentiment=None):
        now = datetime.utcnow().isoformat()

        pnl = ""
        return_pct = ""
        
        # For PnL: store BUYs and SELLs in matched pairs
        if action == 'SELL':
            pnl_val, ret = self.calculate_trade_pnl(amount, price)
            pnl = round(pnl_val, 4)
            # row += [round(pnl_val, 4), round(ret, 4)]
            return_pct = round(ret, 4)
            self.loss_streak += 1 if pnl_val < 0 else 0
        elif action == 'BUY':
            self.loss_streak = 0 # reset streak on BUY
        
        
        log_trade(
            timestamp=now,
            action=action,
            amount=amount,
            price=price,
            confidence=confidence,
            symbol=symbol,
            tx_sig=tx_sig,
            pnl=pnl,
            return_pct=return_pct,
            sentiment=sentiment
        )

            
        self.last_trade_time = datetime.utcnow()


    def calculate_trade_pnl(self, sell_amount, sell_price):
        try:
            # drive = DriveLogger()
            # file_data = drive.download_file(os.path.basename(self.log_file))
            rows = fetch_all_trades()
            # if not file_data:
            #     print(f"[RiskManager] No data downloaded from log file for PnL calculation. Returning 0.0, 0.0")
            #     return 0.0, 0.0

            # reader = csv.reader(io.StringIO(file_data))
            # try:
            #     next(reader)
            # except StopIteration:
            #     print(f"[RiskManager] Log file is empty or only contains header for PnL calculation. Returning 0.0, 0.0")
            #     return 0.0, 0.0

            # with open(self.log_file, mode='r') as f:
            # rows = list(reader)
            for row in reversed(rows): # skip header
                _, action, amount, price, *_ = row
                if action == 'BUY' and abs(amount - sell_amount) < 1e-6:
                # if len(row) < 4:
                #     print(f"[RiskManager] Skipping malformed row {row_idx + 2} in calculate_trade_pnl: {row} - not enough columns")
                #     continue
                # # Check if the row represents a BUY action
                # if row[1] == 'BUY': # and not row[-2]: # match unpaired BUY
                #     try:
                #         # Attempt to convert amount and price to float
                #         buy_amount = float(row[2])
                #         buy_price = float(row[3])
                #         # Checking if BUY approximately matches SELL amount
                #         if abs(buy_amount - sell_amount) < 1e-6:
                    pnl = (sell_price - price) * sell_amount
                    ret = (sell_price - price) / buy_price
                    return round(pnl, 4),  round(ret, 4)
            # except ValueError as ve:
            print(f"[RiskManager] Not matching BUY found for SELL to calculate PnL.")
                    #     continue # Skip this row if amount/price are not floats
                    # except IndexError as ie:
                    #     print(f"[RiskManager] Column access error in calculate trade PnL for row: {row_idx + 2}: {row}. Error: {ie}")
        except Exception as e:
            print(f"[RiskManager] Error calculating trade PnL: {e}")
        return 0.0, 0.0

    def print_summary(self):
        trades = 0
        wins = 0
        losses = 0
        total_pnl = 0
        open_buy_positions = []

        try:
            # Get log from drivelogger
            # drive = DriveLogger()
            # file_data = drive.download_file(self.log_file)
            rows = fetch_all_trades()

            # if file_data is None or not file_data.strip():
            #     print(f"[RiskManager] No data downloaded from log file for summary. Summary skipped.")
            #     return

            # reader = csv.reader(io.StringIO(file_data))

            # # Skip header row
            # try: 
            # # with open(self.log_file, mode='r') as f:
            #     next(reader)
            # except StopIteration:
            #     print(f"[RiskManager] Log file is empty or only contains header for summary. Summary skipped.")
            #     return
            # Iterate through each row in the log file
            for row in rows:
                _, action, amount, price, *_ = row
                # try:
                #     # Ensure the row has at least 4 columns (timestamp, action, amount, price)
                #     if len(row) < 4:
                #         print(f"[RiskManager] Skipping malformed row {row_num} in summary: {row} - not enough columns.")
                #         continue
                    
                #     action = row[1]
                #     amount_str = row[2]
                #     price_str = row[3]

                #     # Attempt to convert amount and price to float
                #     try:
                #         amount = float(amount_str)
                #         price = float(price_str)
                #     except ValueError:
                #         print(f"[RiskManager] Data conversion error in summary for row: {row_num}: {row}. Skipping row.")
                #         continue

                if action == 'BUY':
                    open_buy_positions.append({"amount": amount, "price": price})
                elif action == "SELL":
                    trades += 1 # Count SELL as complete trade for summary purposes

                    # Finding matching buy positions to calculate PnL
                    match = next((i for i, b in enumerate(open_buy_positions) if abs(b["amount"] - amount) < 1e-6), None)
                    if match is not None:
                    # matched_buy_idx = -1
                    # for i, buy_pos in enumerate(open_buy_positions):
                    #     if abs(buy_pos['amount'] - amount) < 1e-6:
                    #         matched_buy_idx = i
                    #         break
                        
                    #     if matched_buy_idx != -1:
                    #         # If matching buy found, removed it.
                        buy = open_buy_positions.pop(match)
                        pnl = (price - buy['price']) * amount
                        total_pnl += pnl
                        if pnl > 0:
                            wins += 1
                        else:
                            losses += 1
                    else:
                        print(f"[RiskManager] Warning: SELL trade at ({amount} @ {price}) could not be matched with a buy position.")
                # except Exception as row_e:
                #     print(f"[RiskManager] Error processing row {row_num} in summary: {row}. Error: {row_e}. Skipping row.")
                #     continue
                    # pnl = row[-2]
                    # if pnl:
                    #     pnl = float(pnl)
                    #     trades += 1
                    #     total_pnl += pnl
                    #     if pnl > 0:
                    #         wins += 1
                    #     else:
                    #         losses += 1
            print(f"\n[Trade Summary]")
            print(f"    Total Trades: {trades}")
            print(f"    Wins: {wins}, Losses: {losses}")
            print(f"    Win Rate: {(wins / trades * 100):.2f}%" if trades > 0 else "    N/A")
            print(f"    Total PnL: {total_pnl:.4f} SOL")

            if open_nuy_positions:
                print(f"    Warning: {len(open_nuy_positions)} unmatched BUY positions remaining in the log.")

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
            # 🔄 Download log file from drive as in-memory string
            # file_data = self.drive.download_file(os.path.basename(self.log_file))
            rows = fetch_all_trades()
            # if not file_data:
            #     print(f"[RiskManager] No data downloaded from log file for daily loss calculation.")
            #     return 0.0

            # reader = csv.reader(io.StringIO(file_data))

            # with open(self.log_file, mode='r') as f:
            # next(reader) # Skipping header
            for row in rows:
                timestamp_str, action, amount, price, *_ = row
                timestamp = datetime.fromisoformat(timestamp_str)
                # if timestamp.date() == today:

                # try:
                #     # Ensure the row has at least 4 columns (timestamp, action, amount, price)
                #     if len(row) < 4:
                #         print(f"[RiskManager] Skipping malformed row {row_num} in summary: {row} - not enough columns.")
                #         continue
                    
                #     timestamp = datetime.fromisoformat(row[0])
                #     action = row[1]
                #     amount_str = row[2]
                #     price_str = row[3]

                #     try:
                #         amount = float(amount_str)
                #     except ValueError:
                #         print(f"[RiskManager] Error converting amount '{amount_str}' to float in row: {row_num}: {row} Skipping row.")
                #         continue

                #     try:
                #         price = float(price_str)
                #     except ValueError:
                        # print(f"[RiskManager] Error converting amount '{price_str}' to float in row: {row_num}: {row} Skipping row.")
                        # continue
                    
                if timestamp.date() == today:
                    # Treat BUY as cost, SELL as profit (for now)
                    if action == 'BUY':
                        loss += amount * price
                    elif action == 'SELL':
                        loss -= amount * price

                # except Exception as row_e:
                #     print(f"[RiskManager] Error processing row '{row_num}' in daily loss: {row}. Error: {row_e} Skipping row.")

        except Exception as e:
            print(f"[RiskManager] Error calculating loss: {e}")
        return round(loss, 4)

    # def approve_trade(self, decision, indicators):
    #     try:
    #         conf = decision.get("confidence", 0)
    #         amount = decision.get("amount", 0)
    #         price = indicators.get("price", 0)

    #         print(f"[RiskManager] Checking: conf={conf}, amount={amount}, price={price}")

    #         if conf < 0.1:
    #             print(f"[RiskManager] Confidence too low.")
    #             return False

    #         if amount * price > self.max_position_size:
    #             print(f"[RiskManager] Trade amoiunt {amount} exceeds max allowed.")
    #             return False

    #         # TODO: More rules here

    #         return True

    #     except Exception as e:
    #         print(f"[RiskManager] Error: {e}")
    #         return False


    def approve_trade(self, decision, indicators):
        if not indicators:
            print(f"[RiskManager] No indicators provided.")
            return False

        action = decision.get("action")
        confidence = decision.get("confidence", 0.0)
        rsi = indicators.get("rsi", 50)
        
        # 1. Only allow high confidence trades
        if confidence < self.min_confidence:
            print(f"[RiskManager] Confidence too low: {confidence}")
            return False
        
        # 2. RSI-Based filter
        if action == 'BUY' and rsi > 70:
            print(f"[RiskManager] RSI too high - market overbought.")
            return False
        if action == 'SELL' and rsi < 30:
            print(f"[RiskManager] RSI too low - market oversold.")
            return False

        if self.is_cooldown_active():
            print(f"[RiskManager] ")
            return False

        # 3. Check daily loss cap
        if confidence < 0.75:
            print(f"[RiskManager] Confidence too low: {confidence}")
            return False

        if self.loss_streak >= self.max_loss_streak:
            print(f"[RiskManager] Trade rejected: max loss streak ({self.loss_streak} reached)")
            return False

        daily_loss = self.calculate_daily_loss()
        if daily_loss > self.max_daily_loss:
            print(f"[RiskManager] Trade rejected due to max daily loss ({daily_loss:.2f} > {self.max_daily_loss})")
            return False


        return True

         
