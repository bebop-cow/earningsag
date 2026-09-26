import requests
import os
from dotenv import load_dotenv

load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def get_earnings(ticker):
	url = f"https://finnhub.io/api/v1/stock/metric"
	params = {"symbol": ticker, "metric": "all", "token": FINNHUB_KEY}
	resp = requests.get(url, params=params)
	return resp.json()

data = get_earnings("NFLX")
m = data["metric"]

summary = {
    "revenue_growth_yoy": m.get("revenueGrowthQuarterlyYoy"),
    "revenue_per_share": m.get("revenuePerShareTTM"),
    "eps_growth_yoy": m.get("epsGrowthQuarterlyYoy"),
    "gross_margin": m.get("grossMarginTTM"),
    "net_margin": m.get("netProfitMarginTTM"),
    "pe_ratio": m.get("peTTM"),
}
print(summary)