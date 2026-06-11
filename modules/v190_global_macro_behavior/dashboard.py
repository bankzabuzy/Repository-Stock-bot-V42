
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import V190_VERSION, now_th, init_db, connect
from .human_behavior_ai import human_behavior_ai
from .economic_ai import economic_ai
from .event_prediction import event_prediction
from .news_sentiment_ai import news_sentiment_ai
from .narrative_engine import market_narrative
from .probability_engine import probability_engine
from .consensus_factcheck import multi_ai_consensus, fact_check_layer
from .black_swan import black_swan_detector

def build_v190_payload():
    init_db()
    payload = {
        "ok": True,
        "version": V190_VERSION,
        "time_th": now_th(),
        "human_behavior_ai": human_behavior_ai(),
        "economic_ai": economic_ai(),
        "event_prediction": event_prediction(),
        "news_sentiment_ai": news_sentiment_ai(),
        "market_narrative": market_narrative(),
        "probability_engine": probability_engine(),
        "multi_ai_consensus": multi_ai_consensus(),
        "fact_check_layer": fact_check_layer(),
        "black_swan_detector": black_swan_detector(),
    }
    final_bias = payload["multi_ai_consensus"].get("consensus")
    confidence = payload["multi_ai_consensus"].get("agreement_pct")
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v190_macro_predictions(created_at,horizon,macro_regime,market_narrative,probability_report,consensus,fact_check,final_bias,confidence,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(),"1D/1W/1M",payload["economic_ai"].get("macro_regime"),payload["market_narrative"].get("narrative"),json.dumps(payload["probability_engine"],ensure_ascii=False,default=str),payload["multi_ai_consensus"].get("consensus"),payload["fact_check_layer"].get("status"),final_bias,confidence,V190_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def build_v190_text():
    p = build_v190_payload()
    h = p["human_behavior_ai"]
    e = p["economic_ai"]
    ev = p["event_prediction"]
    n = p["market_narrative"]
    prob = p["probability_engine"].get("horizons",{})
    cons = p["multi_ai_consensus"]
    fc = p["fact_check_layer"]
    bs = p["black_swan_detector"]
    lines = [
        "🌐 V190 GLOBAL MACRO BEHAVIOR & EVENT PREDICTION ENGINE",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "HUMAN BEHAVIOR AI",
        f"Fear: {h.get('fear_score')} | Greed: {h.get('greed_score')} | Actors: {h.get('actors')}",
        "",
        "ECONOMIC AI",
        f"Macro Regime: {e.get('macro_regime')} | Scores: {e.get('scores')}",
        "",
        "EVENT PREDICTION",
        f"Decision: {ev.get('decision')} | Nearest: {ev.get('nearest_event')}",
        "",
        "MARKET NARRATIVE",
        f"{n.get('narrative')}",
        "",
        "PROBABILITY ENGINE",
        f"1D: {prob.get('1D')}",
        f"1W: {prob.get('1W')}",
        f"1M: {prob.get('1M')}",
        "",
        "MULTI-AI CONSENSUS / FACT CHECK",
        f"Consensus: {cons.get('consensus')} | Agreement: {cons.get('agreement_pct')}% | FactCheck: {fc.get('status')}",
        "",
        "BLACK SWAN",
        f"Level: {bs.get('level')} | Triggers: {bs.get('triggers')}",
        "",
        "Quick: /v190/macro-center-json | /v190/probability | /v190/events | /v190/consensus",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
