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

    history = [
        {"period": q["period"], "eps_actual": q["actual"],
         "eps_estimate": q["estimate"], "surprise_pct": q["surprisePercent"]}
        for q in earnings
    ]

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

def ask_loop(report):
    print("Ask anything about this report (type 'exit' to quit)")
    while True:
        question = input("> ")
        if question.lower() == "exit":
            break

        prompt = f"""Here is an earnings report:
        {report}
        Use ONLY the data provided. If the answer isn't in the data, say so.

        Answer this question about it: {question}"""

        response = ollama.chat(model="llama3.1", messages=[
            {"role": "user", "content": prompt}
        ])
        print(response["message"]["content"])
        print()

# run it
report = get_report("NFLX")
print(summarize(report))
print()
ask_loop(report)