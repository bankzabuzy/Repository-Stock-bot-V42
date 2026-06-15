"""
V1420 Paper Trading Engine
ติดตาม trade จาก signal → บันทึก outcome → คำนวณ win rate จริง
"""
import os, time, json, sqlite3, threading
VERSION = "V1420_UNIFIED_LIVE_TRADING_FINAL"

_DB_PATH = os.getenv("PAPER_DB_PATH","paper_trades.db")
_lock = threading.Lock()

def _conn():
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_paper_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, symbol TEXT, side TEXT, qty INTEGER,
            entry_price REAL, tp1 REAL, tp2 REAL, sl REAL,
            exit_price REAL, exit_ts TEXT, status TEXT,
            pnl REAL, pnl_pct REAL, r_multiple REAL,
            signal_score INTEGER, signal_conf INTEGER,
            notes TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS paper_summary (
            id INTEGER PRIMARY KEY,
            total_trades INTEGER, wins INTEGER, losses INTEGER,
            win_rate REAL, avg_r REAL, total_pnl REAL,
            updated_at TEXT
        )""")
        c.commit()

def open_paper_trade(symbol, side, qty, entry, tp1, tp2, sl,
                     score=50, conf=50, notes="") -> int:
    init_paper_db()
    with _conn() as c:
        cur = c.execute("""INSERT INTO paper_trades
            (ts,symbol,side,qty,entry_price,tp1,tp2,sl,status,signal_score,signal_conf,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (time.strftime("%Y-%m-%d %H:%M:%S"), symbol.upper(), side.upper(),
             qty, entry, tp1, tp2, sl, "OPEN", score, conf, notes))
        c.commit()
        return cur.lastrowid

def close_paper_trade(trade_id:int, exit_price:float, notes:str="") -> dict:
    init_paper_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM paper_trades WHERE id=?", (trade_id,)).fetchone()
        if not row:
            return {"error":f"Trade {trade_id} not found"}
        entry = float(row["entry_price"])
        side  = row["side"]
        qty   = int(row["qty"])
        sl    = float(row["sl"] or 0)
        raw_pnl = (exit_price - entry)*qty if side=="BUY" else (entry-exit_price)*qty
        pnl_pct = (exit_price-entry)/entry*100 if entry else 0
        if side=="SELL": pnl_pct = -pnl_pct
        risk = abs(entry-sl) if sl else max(entry*0.02, 1)
        r_mult = raw_pnl/(risk*qty) if risk*qty else 0
        status = "WIN" if raw_pnl>0 else "LOSS"
        c.execute("""UPDATE paper_trades SET
            exit_price=?,exit_ts=?,status=?,pnl=?,pnl_pct=?,r_multiple=?,notes=notes||?
            WHERE id=?""",
            (exit_price, time.strftime("%Y-%m-%d %H:%M:%S"),
             status, raw_pnl, pnl_pct, r_mult, f" | {notes}", trade_id))
        c.commit()
        _update_summary(c)
        return {"trade_id":trade_id,"status":status,"pnl":raw_pnl,
                "pnl_pct":pnl_pct,"r_multiple":r_mult}

def _update_summary(c):
    rows = c.execute("SELECT status,pnl,r_multiple FROM paper_trades WHERE status IN ('WIN','LOSS')").fetchall()
    if not rows: return
    wins   = sum(1 for r in rows if r["status"]=="WIN")
    losses = sum(1 for r in rows if r["status"]=="LOSS")
    total  = wins+losses
    wr     = wins/total*100 if total else 0
    avg_r  = sum(float(r["r_multiple"] or 0) for r in rows)/len(rows) if rows else 0
    total_pnl = sum(float(r["pnl"] or 0) for r in rows)
    c.execute("""INSERT OR REPLACE INTO paper_summary
        (id,total_trades,wins,losses,win_rate,avg_r,total_pnl,updated_at)
        VALUES (1,?,?,?,?,?,?,?)""",
        (total,wins,losses,wr,avg_r,total_pnl,time.strftime("%Y-%m-%d %H:%M:%S")))
    c.commit()

def get_open_trades() -> list:
    init_paper_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM paper_trades WHERE status='OPEN' ORDER BY ts DESC").fetchall()
        return [dict(r) for r in rows]

def get_paper_summary() -> dict:
    init_paper_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM paper_summary WHERE id=1").fetchone()
        return dict(row) if row else {"total_trades":0,"wins":0,"losses":0,"win_rate":0,"avg_r":0,"total_pnl":0}

def paper_status_text() -> str:
    trades = get_open_trades()
    summ   = get_paper_summary()
    wr     = summ.get("win_rate",0)
    avg_r  = summ.get("avg_r",0)
    total  = summ.get("total_pnl",0)
    wr_e   = "🟢" if wr>=55 else ("🟡" if wr>=45 else "🔴")

    open_lines = ""
    for t in trades[:5]:
        open_lines += (f"\n  #{t['id']} {t['symbol']} {t['side']} "
                      f"| Entry ${t['entry_price']:.2f} "
                      f"| TP1 ${t.get('tp1',0):.2f} SL ${t.get('sl',0):.2f}")

    return (
        f"📋 Paper Trading Summary\n"
        f"Total: {summ.get('total_trades',0)} trades\n"
        f"{wr_e} Win Rate: {wr:.1f}% "
        f"({summ.get('wins',0)}W / {summ.get('losses',0)}L)\n"
        f"Avg R-Multiple: {avg_r:+.2f}R\n"
        f"Total P&L: {'📈' if total>=0 else '📉'} ${total:+,.2f}\n\n"
        f"Open Positions: {len(trades)}{open_lines or ' ไม่มี'}\n\n"
        f"ใช้: 'เปิด NVDA 1' เพื่อเปิด paper trade\n"
        f"ใช้: 'ปิด 1 185.50' เพื่อปิด trade #1\n\n"
        f"Version : {VERSION}"
    )
