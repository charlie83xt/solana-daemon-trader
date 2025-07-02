# agents/agent_orchestrator.py
import csv
from datetime import datetime
import os


class AgentOrchestrator:
    def __init__(self, agents, vote_log="logs/agent_votes.csv"):
        self.agents = agents
        self.vote_log = vote_log
        self._ensure_vote_log()

    
    def _ensure_vote_log(self):
        os.makedirs(os.path.dirname(self.vote_log), exist_ok=True)
        if not os.path.exists(self.vote_log):
            with open(self.vote_log, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "agent", "action", "amount", "confidence"])


    async def resolve_decision(self, indicators):
        votes = []
        for agent in self.agents:
            decision = await agent.get_decision(indicators)
            votes.append((agent.name, decision))
            self._log_vote(agent.name, decision)

        print(f"[AgentOrchestrator] Agent votes:")
        for name, vote in votes:
            print(f"    - {name}: {vote}")

        # Simple majority resolver: BUY > HOLD > SELL
        action_count = {"BUY": 0, "SELL": 0, "HOLD": 0}
        avg_confidence = 0.0
        avg_amount = 0.0

        for _, decision in votes:
            action = decision.get("action", "HOLD")
            action_count[action] += 1
            avg_confidence += decision.get("confidence", 0.0)
            avg_amount += decision.get("amount", 0.0)

        final_action = max(action_count, key=action_count.get)
        n = len(votes)
        return {
            "action": final_action,
            "amount": round((avg_amount / n), 4),
            "confidence": round((avg_confidence / n), 4)
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