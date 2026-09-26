import requests
import os
from dotenv import load_dotenv

load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def get_earnings(ticker):
	url = f"https://finnhub.io/api/v1/stock/earnings"
	params = {"symbol": ticker, "token": FINNHUB_KEY}
	resp = requests.get(url, params=params)
	return = resp.json()

data = get_earnings("NFLX")
print(data)