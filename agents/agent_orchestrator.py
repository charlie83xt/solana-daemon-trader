# agents/agent_orchestrator.py
import csv
from datetime import datetime
import os
from log_router import LogRouter


class AgentOrchestrator:
    def __init__(self, agents, vote_log="logs/agent_votes.csv"):
        self.agents = agents
        self.vote_log = vote_log
        self._ensure_vote_log()
        self.logger = LogRouter(use_drive=True)

    
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

        # Group by action
        grouped = {}
        for _, decision in votes:
            action = decision["action"]
            grouped.setdefault(action, []).append(decision)
            
            # action_count[action] += 1
            # avg_confidence += decision.get("confidence", 0.0)
            # avg_amount += decision.get("amount", 0.0)

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
                amount = amount

        # Majority vote logic
        # actions = [v["action"] for v in votes]
        # final_action = max(set(actions), key=actions.count)

        # agreeing_votes = [v for v in votes if v["action"] == final_action]

        # avg_amount = sum(v["amount"] for v in agreeing_votes) / len(agreeing_votes)
        # avg_confidence = sum(v["confidence"] for v in agreeing_votes) / len(agreeing_votes)

        # print(f"[AgentOrchestrator] Agent votes:")
        # for i, vote in enumerate(votes):
        #     print(f"    - {self.agents[i].name}: {vote}")
        print(f"[Final Decision] {best_action} {amount:.3f} {indicators.get("symbol", "SOL")} @ confidence {best_confidence * 100:.1f}%")

        # Simple majority resolver: BUY > HOLD > SELL
        # action_count = {"BUY": 0, "SELL": 0, "HOLD": 0}
        # avg_confidence = 0.0
        # avg_amount = 0.0

        # for _, decision in votes:
        #     action = decision.get("action", "HOLD")
        #     action_count[action] += 1
        #     avg_confidence += decision.get("confidence", 0.0)
        #     avg_amount += decision.get("amount", 0.0)

        # final_action = max(action_count, key=action_count.get)
        # n = len(votes)
        return {
            "action": best_action,
            "amount": round(amount, 4),
            "confidence": round(best_confidence, 4)
        }
    
    
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