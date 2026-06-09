# V42.5 GOLD INSTITUTIONAL HIGH CONVICTION ROUTES
# Optional blueprint. main.py also exposes direct routes, but this file keeps the module complete.

from flask import Blueprint, jsonify, Response

V42_ROUTE_VERSION = "V42.5_GOLD_US_EXTENDED_EXPLAINABLE_STABLE"
v42_gold_bp = Blueprint("v42_gold", __name__)


@v42_gold_bp.route("/v42/gold", methods=["GET"])
def v42_gold_json():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_payload
        return jsonify(build_v42_gold_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": V42_ROUTE_VERSION, "error": str(e)}), 200


@v42_gold_bp.route("/v42/gold-text", methods=["GET"])
def v42_gold_text():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_text
        return Response(build_v42_gold_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึงระบบ V42.5 GOLD ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


@v42_gold_bp.route("/v42/gold-high-conviction", methods=["GET"])
def v42_gold_high_conviction_text():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_high_conviction_text
        return Response(build_v42_gold_high_conviction_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V42.5 High Conviction ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")



@v42_gold_bp.route("/v42/gold-dashboard", methods=["GET"])
def v42_gold_dashboard_text():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_dashboard_text
        return Response(build_v42_gold_dashboard_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V42.5 Gold Dashboard ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


@v42_gold_bp.route("/v42/gold-fund-grade", methods=["GET"])
def v42_gold_fund_grade_json():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_payload
        payload = build_v42_gold_payload()
        return jsonify({
            "ok": payload.get("ok", False),
            "version": payload.get("version"),
            "time_th": payload.get("time_th"),
            "entry_filter": payload.get("entry_filter"),
            "entry_score": payload.get("entry_score"),
            "economic_calendar_filter": payload.get("economic_calendar_filter"),
            "dxy_bond_yield_filter": payload.get("dxy_bond_yield_filter"),
            "order_block_detection": payload.get("order_block_detection"),
            "liquidity_sweep_detection": payload.get("liquidity_sweep_detection"),
            "winrate_dashboard": payload.get("winrate_dashboard"),
            "self_learning": payload.get("self_learning"),
            "engine": payload.get("engine"),
            "trade_plan": payload.get("trade_plan"),
            "push_alert": payload.get("push_alert"),
            "raw_confidence": payload.get("raw_confidence"),
            "final_confidence": payload.get("final_confidence"),
            "explainable_ai": payload.get("explainable_ai"),
            "us_stock_extended_hours": payload.get("us_stock_extended_hours"),
            "market_breadth": payload.get("market_breadth"),
        })
    except Exception as e:
        return jsonify({"ok": False, "version": V42_ROUTE_VERSION, "error": str(e)}), 200


@v42_gold_bp.route("/thai-gold", methods=["GET"])
def thai_gold_json():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_payload
        payload = build_v42_gold_payload()
        return jsonify({
            "ok": payload.get("ok", False),
            "version": payload.get("version"),
            "time_th": payload.get("time_th"),
            "thai_gold": payload.get("thai_gold"),
            "engine": payload.get("engine"),
            "trade_plan": payload.get("trade_plan"),
            "entry_score": payload.get("entry_score"),
            "entry_filter": payload.get("entry_filter"),
        })
    except Exception as e:
        return jsonify({"ok": False, "version": V42_ROUTE_VERSION, "error": str(e)}), 200


@v42_gold_bp.route("/v42/gold-filter", methods=["GET"])
def v42_gold_filter():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_payload
        payload = build_v42_gold_payload()
        return jsonify({
            "ok": payload.get("ok", False),
            "version": payload.get("version"),
            "time_th": payload.get("time_th"),
            "entry_filter": payload.get("entry_filter"),
            "entry_score": payload.get("entry_score"),
            "session_filter": payload.get("session_filter"),
            "high_impact_news_filter": payload.get("high_impact_news_filter"),
            "spread_filter": payload.get("spread_filter"),
            "strong_buy": payload.get("strong_buy"),
            "smart_trailing_stop": payload.get("smart_trailing_stop"),
            "engine": payload.get("engine"),
            "trade_plan": payload.get("trade_plan"),
            "push_alert": payload.get("push_alert"),
            "raw_confidence": payload.get("raw_confidence"),
            "final_confidence": payload.get("final_confidence"),
            "explainable_ai": payload.get("explainable_ai"),
            "us_stock_extended_hours": payload.get("us_stock_extended_hours"),
            "market_breadth": payload.get("market_breadth"),
        })
    except Exception as e:
        return jsonify({"ok": False, "version": V42_ROUTE_VERSION, "error": str(e)}), 200


@v42_gold_bp.route("/v42/gold-explain", methods=["GET"])
def v42_gold_explain_text():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_explainable_text
        return Response(build_v42_gold_explainable_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V42.5 Explainable AI ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


@v42_gold_bp.route("/v42/us-extended-hours", methods=["GET"])
def v42_us_extended_hours_text():
    try:
        from flask import request
        from modules.v42_gold_institutional_core import build_us_extended_hours_text
        symbols_raw = request.args.get("symbols", "")
        symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()] if symbols_raw else None
        return Response(build_us_extended_hours_text(symbols), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง US Extended Hours ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


@v42_gold_bp.route("/v42/market-breadth", methods=["GET"])
def v42_market_breadth_text():
    try:
        from modules.v42_gold_institutional_core import build_market_breadth_text
        return Response(build_market_breadth_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง Market Breadth ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

