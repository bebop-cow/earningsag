import requests
import os
from dotenv import load_dotenv
import ollama
from garch import vol_summary
print(vol_summary("NFLX"))

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
        "eps_history": history,
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

def get_statements(ticker):
    url = "https://finnhub.io/api/v1/stock/financials-reported"
    params = {"symbol": ticker, "freq": "quarterly", "token": FINNHUB_KEY}
    return requests.get(url, params=params).json()

def find_value(section, keywords):
    for item in section:
        text = (item["concept"] + " " + item["label"]).lower()
        if any(k in text for k in keywords):
            return item["value"]
    return None

def metric_history(data, statement, keywords):
    return [
        (q["year"], q["quarter"], q["form"],
         find_value(q["report"][statement], keywords))
        for q in data["data"]
    ]

data = get_statements("NFLX")

def to_quarterly(rows):
    ytd = {(y, q): v for y, q, f, v in rows if v is not None}
    out = {}
    for (y, q), v in ytd.items():
        if q == 1:
            out[(y, q)] = v
        elif (y, q - 1) in ytd:
            out[(y, q)] = v - ytd[(y, q - 1)]
    return out

content = to_quarterly(metric_history(data, "cf", ["additions to content"]))
for k in [(2025, 1), (2025, 2), (2025, 3), (2026, 1)]:
    print(k, content[k])

def analyze(ticker):
    data = get_statements(ticker)
    flags = []

    # spending + net income (cash flow is YTD, so convert)
    content = to_quarterly(metric_history(data, "cf", ["additions to content"]))
    ni = to_quarterly(metric_history(data, "cf", ["net income"]))
    k = max(content)
    prev = (k[0] - 1, k[1])
    spend_yoy = (content[k] / content[prev] - 1) * 100
    ni_yoy = (ni[k] / ni[prev] - 1) * 100

    # EPS growth (from Finnhub) vs net income growth
    eps_yoy = get_revenue(ticker)["metric"].get("epsGrowthQuarterlyYoy")
    if eps_yoy is not None and abs(ni_yoy - eps_yoy) > 25:
        flags.append(f"Net income {ni_yoy:+.0f}% YoY but EPS {eps_yoy:+.0f}%: possible one-time item")

    # net debt (balance sheet is a snapshot, no conversion)
    def bs(kw):
        return {(y, q): v for y, q, f, v in metric_history(data, "bs", kw) if v is not None}
    lt, st, cash = bs(["long-term debt"]), bs(["short-term debt"]), bs(["cash and cash equivalents"])
    nd = lambda p: lt.get(p, 0) + st.get(p, 0) - cash[p]
    nd_change = (nd(k) / nd(prev) - 1) * 100

    if spend_yoy > 20:
        flags.append(f"Content spend up {spend_yoy:.0f}% YoY")
    if nd_change > ????:      # your call: what % rise in net debt is worth flagging?
        flags.append(f"Net debt up {nd_change:.0f}% YoY")

    return {
        "period": f"{k[0]} Q{k[1]}",
        "content_spend_yoy_pct": round(spend_yoy, 1),
        "net_income_yoy_pct": round(ni_yoy, 1),
        "net_debt_bn": round(nd(k) / 1e9, 2),
        "net_debt_change_yoy_pct": round(nd_change, 1),
        "flags": flags,
    }

print(analyze("NFLX"))
# run it
# report = get_report("NFLX")
# print(summarize(report))
# print()
# ask_loop(report)