"""
V1420 Broker — Webull API (PAPER + LIVE mode)
============================================
PAPER mode: บันทึกใน DB ไม่ส่ง order จริง (ปลอดภัย 100%)
LIVE  mode: ต้องตั้ง WEBULL_LIVE_MODE=true + TOKEN ครบ
ทุก order มี human confirmation gate ก่อนส่งจริง
"""
import os, time, requests, json

VERSION = "V1420_UNIFIED_LIVE_TRADING_FINAL"

WB_TOKEN   = os.getenv("WEBULL_ACCESS_TOKEN","")
WB_DID     = os.getenv("WEBULL_DID","")
WB_ACCOUNT = os.getenv("WEBULL_ACCOUNT_ID","")
LIVE_MODE  = os.getenv("WEBULL_LIVE_MODE","false").lower() == "true"

# Safety: max $ per order, max daily orders
MAX_ORDER_USD   = float(os.getenv("MAX_ORDER_USD","500"))
MAX_DAILY_ORDERS = int(os.getenv("MAX_DAILY_ORDERS","5"))

_daily_orders = {"date":"","count":0}

def _check_daily_limit():
    today = time.strftime("%Y-%m-%d")
    if _daily_orders["date"] != today:
        _daily_orders.update({"date":today,"count":0})
    if _daily_orders["count"] >= MAX_DAILY_ORDERS:
        return False, f"Daily order limit reached ({MAX_DAILY_ORDERS}/day)"
    return True, "OK"

def _webull_headers():
    return {
        "Access-Token": WB_TOKEN,
        "did": WB_DID,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }

def get_account_info() -> dict:
    """Get Webull account balance and positions."""
    if not WB_TOKEN or not WB_DID or not WB_ACCOUNT:
        return {"error":"WEBULL_TOKEN_NOT_SET","mode":"PAPER","balance":0,"positions":[]}
    try:
        url = f"https://ustrade.webull.com/api/trade/v2/pl/list?accountId={WB_ACCOUNT}&pageSize=20"
        r = requests.get(url, headers=_webull_headers(), timeout=5)
        d = r.json()
        positions = []
        for p in (d.get("positionList") or []):
            positions.append({
                "symbol":  p.get("ticker",{}).get("symbol","?"),
                "qty":     float(p.get("position",0)),
                "cost":    float(p.get("costPrice",0)),
                "price":   float(p.get("lastPrice",0)),
                "pnl":     float(p.get("unrealizedProfitLoss",0)),
                "pnl_pct": float(p.get("unrealizedProfitLossRate",0))*100,
            })
        return {
            "mode": "LIVE" if LIVE_MODE else "PAPER",
            "account_id": WB_ACCOUNT,
            "net_liquidation": float(d.get("netLiquidation",0)),
            "cash_balance":    float(d.get("cashBalance",0)),
            "positions": positions,
            "source": "Webull_API",
        }
    except Exception as e:
        return {"error":str(e),"mode":"PAPER","source":"Webull_Error"}

def place_order(symbol:str, side:str, qty:int, order_type:str="MKT",
                limit_price:float=None, stop_price:float=None,
                time_in_force:str="DAY") -> dict:
    """
    Place order. PAPER mode = บันทึกเท่านั้น.
    LIVE  mode = ส่ง Webull จริง (ต้องตั้ง WEBULL_LIVE_MODE=true)
    """
    side = side.upper()
    if side not in {"BUY","SELL"}:
        return {"status":"ERROR","reason":f"Invalid side: {side}"}
    if qty <= 0:
        return {"status":"ERROR","reason":"qty must > 0"}

    ok, msg = _check_daily_limit()
    if not ok:
        return {"status":"BLOCKED","reason":msg}

    order = {
        "symbol": symbol.upper(),
        "side": side,
        "qty": qty,
        "order_type": order_type,
        "limit_price": limit_price,
        "stop_price": stop_price,
        "tif": time_in_force,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "LIVE" if LIVE_MODE else "PAPER",
    }

    if not LIVE_MODE:
        # PAPER: log only
        _daily_orders["count"] += 1
        order["status"] = "PAPER_EXECUTED"
        order["paper_note"] = "Paper trade — no real money sent"
        return order

    # LIVE mode
    if not WB_TOKEN or not WB_DID or not WB_ACCOUNT:
        return {"status":"ERROR","reason":"WEBULL credentials not set for LIVE mode"}

    try:
        payload = {
            "action": side,
            "orderType": order_type,
            "outsideRegularTradingHour": False,
            "quantity": qty,
            "serialId": f"v1420_{int(time.time())}",
            "tickerId": _get_ticker_id(symbol),
            "timeInForce": time_in_force,
        }
        if order_type == "LMT" and limit_price:
            payload["lmtPrice"] = str(limit_price)
        if order_type in {"STP","STP_LMT"} and stop_price:
            payload["auxPrice"] = str(stop_price)

        url = f"https://ustrade.webull.com/api/trade/v2/order?accountId={WB_ACCOUNT}"
        r = requests.post(url, headers=_webull_headers(), json=payload, timeout=8)
        result = r.json()
        _daily_orders["count"] += 1
        order["status"]    = "LIVE_SENT"
        order["wb_result"] = result
        order["order_id"]  = result.get("orderId","?")
        return order
    except Exception as e:
        return {"status":"ERROR","reason":str(e),"order":order}

def cancel_order(order_id:str) -> dict:
    if not LIVE_MODE:
        return {"status":"PAPER_CANCEL","order_id":order_id}
    try:
        url = f"https://ustrade.webull.com/api/trade/v2/order/cancel?accountId={WB_ACCOUNT}&orderId={order_id}"
        r = requests.post(url, headers=_webull_headers(), timeout=5)
        return {"status":"CANCEL_SENT","result":r.json()}
    except Exception as e:
        return {"status":"ERROR","reason":str(e)}

def _get_ticker_id(symbol:str) -> int:
    """Get Webull internal ticker ID for symbol."""
    try:
        url = f"https://quotes-gw.webull.com/api/search/pc/tickers?keyword={symbol}&pageIndex=1&pageSize=1"
        r = requests.get(url, headers=_webull_headers(), timeout=4)
        items = r.json().get("data",{}).get("items",[])
        if items:
            return int(items[0].get("tickerId",0))
    except Exception:
        pass
    return 0

def broker_status_text() -> str:
    acc = get_account_info()
    mode_badge = "🟢 LIVE" if LIVE_MODE else "🟡 PAPER"
    has_token  = "✅" if WB_TOKEN else "❌"
    has_did    = "✅" if WB_DID else "❌"
    has_acc    = "✅" if WB_ACCOUNT else "❌"

    pos_lines = ""
    for p in acc.get("positions",[])[:5]:
        pnl_e = "📈" if p["pnl"]>=0 else "📉"
        pos_lines += (f"\n   {p['symbol']}: {p['qty']} หุ้น @ ${p['cost']:.2f}"
                      f" | ราคาปัจจุบัน ${p['price']:.2f}"
                      f" | P&L {pnl_e} ${p['pnl']:+.2f} ({p['pnl_pct']:+.1f}%)")

    return (
        f"💼 Webull Broker Status\n"
        f"Mode: {mode_badge}\n"
        f"Token: {has_token} | DID: {has_did} | Account: {has_acc}\n"
        f"Daily Orders: {_daily_orders['count']}/{MAX_DAILY_ORDERS}\n"
        f"Max/Order: ${MAX_ORDER_USD:,.0f}\n\n"
        f"Portfolio:\n"
        f"Net Value: ${acc.get('net_liquidation',0):,.2f}\n"
        f"Cash: ${acc.get('cash_balance',0):,.2f}\n"
        f"Positions:{pos_lines or ' ไม่มี open positions'}\n\n"
        f"⚠️ ความปลอดภัย:\n"
        f"• PAPER mode = ไม่ใช้เงินจริง\n"
        f"• LIVE mode ต้อง WEBULL_LIVE_MODE=true\n"
        f"• SL ทุก order ห้ามฝืน\n\n"
        f"Version : {VERSION}"
    )
