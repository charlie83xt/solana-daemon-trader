# agents/agent_orchestrator.py
import csv
from datetime import datetime
import os
from log_router import LogRouter
from performance_monitor import PerformanceMonitor
from log_paths import VOTE_LOG


class AgentOrchestrator:
    def __init__(self, agents, vote_log=None):
        self.agents = agents
        self.vote_log = vote_log or VOTE_LOG
        self.logger = LogRouter(use_drive=True)
        self._ensure_vote_log()
        
        self.monitor = PerformanceMonitor()
    
    def _ensure_vote_log(self):
        os.makedirs(os.path.dirname(self.vote_log), exist_ok=True)
        if not os.path.exists(self.vote_log):
            with open(self.vote_log, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "agent", "action", "amount", "confidence"])
                self.logger.log_local_and_remote(self.vote_log)


    async def resolve_decision(self, indicators) -> dict:
        self._ensure_vote_log()
        votes = []

        for agent in self.agents:
            try:
                decision = await agent.get_decision(indicators)
                # votes.append((agent.name, decision))
                votes.append((agent.__class__.__name__, decision))
                self._log_vote(agent.__class__.__name__, decision)
            except Exception as e:
                print(f"[AgentOrchestrator] Agent error: {e}")

        if not votes:
            print(f"[AgentOrchestrator] Not valid agent votes.")
            return {"action": "HOLD", "amount": 0.0, "confidence": 0.0}

        # Evaluate past performance and adapt threshold
        performance = self.monitor.evaluate()
        if performance:
            print(f"[PerformanceMonitor] Recent stats: {performance}")
            for agent in self.agents:
                if agent.__class__.__name__ == "ThresholdAgent":
                    old_threshold = getattr(agent, "conf_threshold", None)
                    if performance["win_rate"] < 0.5:
                        agent.conf_threshold = 0.75
                    elif performance["win_rate"] > 0.8:
                        agent.conf_threshold = 0.4
                    else:
                        agent.conf_threshold = 0.6
                    if old_threshold != agent.conf_threshold:
                        print(f"[PerformanceMonitor] Threshold adjusted from {old_threshold} to {agent.conf_threshold}")

        # Group by decisions by action type
        grouped = {}
        for _, decision in votes:
            action = decision["action"]
            grouped.setdefault(action, []).append(decision)

        # Weighted average
        def weighted_average(vote_list):
            total_weight = sum(v["confidence"] for v in vote_list)
            if total_weight == 0:
                return 0.0, 0.0
            weighted_amount = sum(v["amount"] * v["confidence"] for v in vote_list) / total_weight
            weighted_conf = total_weight / len(vote_list)
            return weighted_amount, weighted_conf

        base_action = None
        best_confidence = -1
        best_amount = 0.0

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

        print(f"[Final Decision] {best_action} {amount:.3f} {indicators.get('symbol', 'SOL')} @ confidence {best_confidence * 100:.1f}%")

        return final_decision
    
    
    def _log_vote(self, agent_name, decision):
        now = datetime.utcnow().isoformat()
        with open(self.vote_log, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                now,
                agent_name,
                decision.get("action", "HOLD"),
                decision.get("amount", 0.0),
                decision.get("confidence", 0.0)
            ])
            try:
                self.logger.log_local_and_remote(self.vote_log)
            except Exception as e:
                print(f"[DriveLogger] in AgentOrchestrator Failed to sync: {e}")