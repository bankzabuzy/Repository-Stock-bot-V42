from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json, sqlite3, os

@dataclass
class JournalEntry:
    symbol: str
    asset_type: str
    signal: str
    price: float | None = None
    confidence: float | None = None
    probability: float | None = None
    risk_grade: str | None = None
    market_regime: str | None = None
    source: str | None = None
    reason: str | None = None
    result_r: float | None = None
    ts: str = ""

class JournalAI:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv("JOURNAL_DB_PATH", "v1400_journal.db")
        self._memory_con = sqlite3.connect(":memory:") if self.db_path == ":memory:" else None
        self._init_db()

    def _connect(self):
        return self._memory_con if self._memory_con is not None else sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                symbol TEXT,
                asset_type TEXT,
                signal TEXT,
                price REAL,
                confidence REAL,
                probability REAL,
                risk_grade TEXT,
                market_regime TEXT,
                source TEXT,
                reason TEXT,
                result_r REAL,
                raw_json TEXT
            )
            """)
            con.commit()

    def add(self, entry: JournalEntry | dict):
        if isinstance(entry, dict):
            entry = JournalEntry(**{k:v for k,v in entry.items() if k in JournalEntry.__dataclass_fields__})
        if not entry.ts:
            entry.ts = datetime.now(timezone.utc).isoformat()
        raw = asdict(entry)
        with self._connect() as con:
            con.execute("""
            INSERT INTO journal_entries
            (ts,symbol,asset_type,signal,price,confidence,probability,risk_grade,market_regime,source,reason,result_r,raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (entry.ts, entry.symbol, entry.asset_type, entry.signal, entry.price, entry.confidence,
                  entry.probability, entry.risk_grade, entry.market_regime, entry.source, entry.reason,
                  entry.result_r, json.dumps(raw, ensure_ascii=False)))
            con.commit()
        return raw

    def summary(self):
        with self._connect() as con:
            rows = con.execute("SELECT signal, result_r, confidence, probability, risk_grade FROM journal_entries").fetchall()
        total = len(rows)
        closed = [r for r in rows if r[1] is not None]
        if not total:
            return {"total":0,"closed":0,"win_rate":None,"expectancy_r":None,"pf":None,"note":"ยังไม่มีรายการ journal"}
        if closed:
            wins = [r[1] for r in closed if r[1] > 0]
            losses = [abs(r[1]) for r in closed if r[1] < 0]
            win_rate = round(len(wins)/len(closed)*100,2)
            expectancy = round(sum(r[1] for r in closed)/len(closed),3)
            pf = round(sum(wins)/(sum(losses) or 1e-9),3)
        else:
            win_rate = expectancy = pf = None
        return {"total":total,"closed":len(closed),"win_rate":win_rate,"expectancy_r":expectancy,"pf":pf}

    def ai_lessons(self):
        s = self.summary()
        if s["total"] == 0:
            return ["ยังไม่มีข้อมูลพอให้ Journal AI สรุปบทเรียน"]
        lessons = []
        if s.get("pf") is not None and s["pf"] < 1.2:
            lessons.append("PF ต่ำกว่า 1.2: ควรลดจำนวนสัญญาณหรือเพิ่ม Risk Gate")
        if s.get("expectancy_r") is not None and s["expectancy_r"] < 0:
            lessons.append("Expectancy ติดลบ: ตรวจสาเหตุจาก entry timing และ regime filter")
        if not lessons:
            lessons.append("Journal ยังไม่พบจุดอ่อนรุนแรง แต่ควรเก็บ forward test ต่อเนื่อง")
        return lessons
