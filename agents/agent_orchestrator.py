# agents/agent_orchestrator.py
import csv
from datetime import datetime
import os
from collections import defaultdict
# from log_router import LogRouter
from performance_monitor import PerformanceMonitor
# from log_paths import VOTE_LOG
from db_logger import log_agent_votes
import sqlite3
from db import get_connection


class AgentOrchestrator:
    def __init__(self, agents, db_path="trading.db"):
        self.agents = agents
        self.db_path = db_path
        # self.logger = LogRouter(use_drive=True)
        self._ensure_vote_table()
        
        self.monitor = PerformanceMonitor()
    
    # def _ensure_vote_log(self):
    #     os.makedirs(os.path.dirname(self.vote_log), exist_ok=True)
    #     if not os.path.exists(self.vote_log):
    #         with open(self.vote_log, mode='w', newline='') as f:
    #             writer = csv.writer(f)
    #             writer.writerow(["timestamp", "agent", "action", "amount", "confidence"])
    #             self.logger.log_local_and_remote(self.vote_log)
    
    def _ensure_vote_table(self):
        # conn = sqlite3.connect(self.db_path)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_votes (
                timestamp TEXT NOT NULL,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                amount FLOAT,
                confidence FLOAT,
                symbol TEXT
            )
        """)
        conn.commit()
        conn.close()



    async def resolve_decision(self, indicators) -> dict:
        # self._ensure_vote_log()
        # print(f"[AgentOrchestrator] Indicators received: {indicators}")
        votes = []

        for agent in self.agents:
            try:
                decision = await agent.get_decision(indicators)
                print(f"[AgentOrchestrator] Vote from {agent.__class__.__name__}: {decision}")
                if decision["action"] in ("BUY", "SELL") and decision["confidence"] > 0:
                    agent_name = agent.__class__.__name__
                    votes.append((agent_name, decision))
                # print(f"[AgentOrchestrator] Vote from {agent.__class__.__name__}: {decision}")
                
                # votes.append((agent.__class__.__name__, decision))
                    self._log_vote(agent.__class__.__name__, decision, indicators.get("symbol"))
                else:
                    print(f"[AgentOrchestrator] Ignored vote from {agent.__class__.__name__}: {decision}")
            except Exception as e:
                print(f"[AgentOrchestrator] Agent error from {agent.__class__.__name__}: {e}")

        valid_votes = [v for _, v in votes if v.get("action") in ("BUY", "SELL") and v.get("confidence", 0) > 0]
        if not valid_votes:
            # print(f"[AgentOrchestrator] Not valid BUY/SELL agent votes with confidence.")
            return {"action": "HOLD", "amount": 0.0, "confidence": 0.0}

        if not votes:
            # print(f"[AgentOrchestrator] Not valid agent votes.")
            return {"action": "HOLD", "amount": 0.0, "confidence": 0.0}

        # Evaluate past performance and adapt threshold
        performance = self.monitor.evaluate()
        if performance:
            # print(f"[PerformanceMonitor] Recent stats: {performance}")
            for agent in self.agents:
                if agent.__class__.__name__ == "ThresholdAgent":
                    old_threshold = getattr(agent, "conf_threshold", None)
                    win_rate = performance["win_rate"]
                    agent.conf_threshold = 0.75 if win_rate < 0.5 else 0.4 if win_rate > 0.8 else 0.6
                    #     agent.conf_threshold = 0.75
                    # elif performance["win_rate"] > 0.8:
                    #     agent.conf_threshold = 0.4
                    # else:
                    #     agent.conf_threshold = 0.6
                    if old_threshold != agent.conf_threshold:
                        # print(f"[PerformanceMonitor] Threshold adjusted from {old_threshold} to {agent.conf_threshold}")
                        continue

        # Group by decisions by action type
        grouped = defaultdict(list)
        for _, decision in votes:
            action = decision["action"]
            grouped[decision["action"]].append(decision)

        # Weighted average
        def weighted_average(vote_list):
            if not vote_list:
                raise ValueError("No valid votes to aggregate")
                # return 0.0, 0.0
            total_weight = sum(v["confidence"] for v in vote_list)
            if total_weight == 0:
                return 0.0, 0.0
            weighted_amount = sum(v["amount"] * v["confidence"] for v in vote_list) / total_weight
            weighted_conf = total_weight / len(vote_list)
                
            return weighted_amount, weighted_conf

        base_action = None
        best_confidence = -1
        best_amount = 0.0

        for _, decision in votes:
            action = decision["action"]
            grouped.setdefault(action, []).append(decision)

        for action, decisions in grouped.items():
            amount, conf = weighted_average(decisions)
            if conf > best_confidence:
                best_confidence = conf
                best_action = action
                best_amount = amount

        final_decision = {
            "action": best_action,
            "amount": round(best_amount, 4),
            "confidence": round(best_confidence, 4)
        }

        # print(f"[Final Decision] {best_action} {amount:.3f} {indicators.get('symbol', 'SOL')} @ confidence {best_confidence * 100:.1f}%")

        return final_decision
    
    
    def _log_vote(self, agent_name, decision, symbol):
        now = datetime.utcnow().isoformat()
        try:
            # with sqlite3.connect("trading.db") as conn:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_votes (timestamp, agent, action, amount, confidence, symbol)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    now,
                    agent_name,
                    decision.get("action", "HOLD"),
                    decision.get("amount", 0.0),
                    decision.get("confidence", 0.0),
                    symbol
                ))
                conn.commit()
        # log_agent_votes
        # with open(self.vote_log, mode='a', newline='') as f:
        #     writer = csv.writer(f)
        #     writer.writerow([
        #         now,
        #         agent_name,
        #         decision.get("action", "HOLD"),
        #         decision.get("amount", 0.0),
        #         decision.get("confidence", 0.0)
        #     ])
        #     try:
        #         self.logger.log_local_and_remote(self.vote_log)
        except Exception as e:
            print(f"[AgentOrchestrator] Failed to log vote to DB: {e}")