"""Quick manual harness for MarketAnalysisAgent."""
import os

import certifi

# Ensure libcurl (used by yfinance) can find trusted CAs on macOS.
ca_bundle = certifi.where()
os.environ.setdefault("CURL_CA_BUNDLE", ca_bundle)
os.environ.setdefault("SSL_CERT_FILE", ca_bundle)

from src.agents.market_agent import MarketAnalysisAgent


def main() -> None:
    agent = MarketAnalysisAgent(ttl=60)
    samples = ["AAPL", "TSLA", "INVALIDTICKER123"]

    for sample in samples:
        response = agent.run(sample)
        print(f"Input: {sample} -> {response.answer} {response.sources}")


if __name__ == "__main__":
    main()
