import requests
import os
from dotenv import load_dotenv
import ollama

load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def get_earnings(ticker):
    url = f"https://finnhub.io/api/v1/stock/earnings"
    params = {"symbol": ticker, "token": FINNHUB_KEY}
    resp = requests.get(url, params=params)
    return resp.json()

def get_revenue(ticker):
    url = "https://finnhub.io/api/v1/stock/metric"
    params = {"symbol": ticker, "metric": "all", "token": FINNHUB_KEY}
    resp = requests.get(url, params=params)
    return resp.json()

data = get_revenue("NFLX")
print(data.keys())

def get_report(ticker):
    earnings = get_earnings(ticker)
    metrics = get_revenue(ticker)["metric"]

    latest = earnings[0]  # most recent quarter

    return {
        "ticker": ticker,
        "period": latest["period"],
        "eps_actual": latest["actual"],
        "eps_estimate": latest["estimate"],
        "eps_surprise_pct": latest["surprisePercent"],
        "revenue_growth_yoy": metrics.get("revenueGrowthQuarterlyYoy"),
        "gross_margin": metrics.get("grossMarginTTM"),
        "net_margin": metrics.get("netProfitMarginTTM"),
    }

def summarize(report):
	prompt = f"""Summarize this earning report in 2-3 plain English sentences, hightlighting whether it beat or missed expectations and any notable trend:
	{report}"""

	response = ollama.chat(model="llama3.1", messages=[
		{"role": "user", "content":prompt}
		])
	return response["message"]["content"]

print(summarize(get_report("NFLX")))