# agents/base_agent.py
class BaseAgent:
    def __init__(self, name):
        self.name = name

    
    async def get_decision(self, indicators):
        raise NotImplementedError("Must implement get_decision() in subclass")

 