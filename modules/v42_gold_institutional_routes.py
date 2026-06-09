# V42.3 GOLD INSTITUTIONAL HIGH CONVICTION ROUTES
# Optional blueprint. main.py also exposes direct routes, but this file keeps the module complete.

from flask import Blueprint, jsonify, Response

V42_ROUTE_VERSION = "V42.3_GOLD_INSTITUTIONAL_HIGH_CONVICTION_STABLE"
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
        return Response(f"ไม่สามารถดึงระบบ V42.3 GOLD ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


@v42_gold_bp.route("/v42/gold-high-conviction", methods=["GET"])
def v42_gold_high_conviction_text():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_high_conviction_text
        return Response(build_v42_gold_high_conviction_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V42.3 High Conviction ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


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
        })
    except Exception as e:
        return jsonify({"ok": False, "version": V42_ROUTE_VERSION, "error": str(e)}), 200
