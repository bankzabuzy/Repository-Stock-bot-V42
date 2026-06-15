VERSION = "V1419_MASTER_CLEAN_FINAL"

# Lightweight global universe for free/Railway runtime.
# Designed to be extended to full S&P500/Nasdaq/SET100 via API/list files.
US_CORE = [
    "NVDA","MSFT","AAPL","AMZN","GOOGL","META","TSLA","AMD","AVGO","TSM",
    "MU","SMCI","NFLX","COST","CRM","ORCL","ADBE","PLTR","CRWD","NOW",
    "JPM","BAC","GS","MS","V","MA","UNH","LLY","NVO","XOM","CVX"
]
ETF_CORE = [
    "QQQ","SPY","IWM","DIA","XLK","SMH","SOXX","XLF","XLE","XLV","XLY","XLP",
    "TLT","GLD","SLV","TQQQ","SQQQ","SOXL","SOXS"
]
TH_CORE = [
    "SCB.BK","KBANK.BK","BBL.BK","KTB.BK","PTT.BK","PTTEP.BK","AOT.BK",
    "ADVANC.BK","CPALL.BK","BDMS.BK","DELTA.BK","TRUE.BK","GULF.BK","CPN.BK",
    "BGRIM.BK","MINT.BK","SCC.BK","TOP.BK","TISCO.BK","HMPRO.BK"
]
GOLD_CORE = ["GOLD"]

def get_universe(kind="GLOBAL"):
    k = (kind or "GLOBAL").upper()
    if k in {"US","USA"}:
        return US_CORE
    if k == "ETF":
        return ETF_CORE
    if k in {"TH","THAI","SET"}:
        return TH_CORE
    if k == "GOLD":
        return GOLD_CORE
    return US_CORE + ETF_CORE + TH_CORE + GOLD_CORE

def universe_size_text():
    return f"US {len(US_CORE)} | ETF {len(ETF_CORE)} | TH {len(TH_CORE)} | GOLD {len(GOLD_CORE)} | รวม {len(get_universe())}"
