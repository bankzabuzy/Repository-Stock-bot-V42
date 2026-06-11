
from __future__ import annotations
from .common import V230_VERSION, now_th, init_db
from .daily_ops import daily_ops_report, daily_ops_text
from .compatibility import compatibility_report

def build_v230_payload():
    init_db()
    return {"ok": True, "version": V230_VERSION, "time_th": now_th(), "daily_ops": daily_ops_report(), "compatibility": compatibility_report(True)}

def build_v230_text():
    p = build_v230_payload()
    comp = p["compatibility"]
    return daily_ops_text() + "\n\nCompatibility: imports=%s routes=%s collisions=%s" % (
        "OK" if comp["imports"]["ok"] else "CHECK",
        comp["routes"]["route_count"],
        comp["routes"]["collision_count"],
    )
