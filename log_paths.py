import os


BASE_DIR = os.environ.get("BASE_DIR", ".")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

TRADE_LOG = os.path.join(LOG_DIR, "trade_log.csv")
VOTE_LOG = os.path.join(LOG_DIR, "agent_votes.csv")
PRICE_LOG = os.path.join(LOG_DIR, "sol_price_history.csv") 

def get_log_path(filename):
    return os.path.join(BASE_DIR, filename)