💡 What it is:
An autonomous trader that uses live market data, technical indicators, and multiple AI agents to make, evaluate, and execute trade decisions on Solana — safely, securely, and without human intervention.

🧲 Live data extraction --=> Fetches real-time SOL/USDC prices and historical data from CoinGecko
📊 Indicator computation	--=> Calculates key technical indicators like SMA, RSI, MACD using pandas-ta
🧠 AI agent ensemble	--=> Combines multiple AI decision-makers — including OpenAI and a rule-based agent — to "vote" on whether to BUY, SELL, or HOLD
🤖 Decision orchestration	--=> Resolves those agent votes into a final decision based on weighted confidence
🔐 Risk management	--=> Enforces daily loss limits, cooldowns, and confidence thresholds to protect your funds
💰 On-chain execution	--=> Executes real transactions on Solana Devnet using your wallet, and can switch to mainnet with a config change
🧾 Trade logging & PnL --=> tracking	Records every trade and calculates profit/loss, win rate, and other metrics
🔁 Autonomous loop	--=> Runs continuously as a daemonized job, making one smart decision every few minutes without supervision

🧭 Vision in Progress
Right now, it trades only SOL, but it’s designed to:

💡 Add support for multiple tokens (e.g. JUP, PYTH, WIF)

🧠 Plug in more advanced agents (e.g. sentiment analysis, on-chain data, news impact)

💼 Eventually make data-driven portfolio decisions, like a mini quant hedge fund — but running 24/7, fully on-chain
