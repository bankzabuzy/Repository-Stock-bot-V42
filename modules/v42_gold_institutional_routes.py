# V42.1 GOLD INSTITUTIONAL ROUTES
# Optional blueprint. main.py also exposes direct routes, but this file makes the module complete.

from flask import Blueprint, jsonify, Response

v42_gold_bp = Blueprint("v42_gold", __name__)


@v42_gold_bp.route("/v42/gold", methods=["GET"])
def v42_gold_json():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_payload
        return jsonify(build_v42_gold_payload())
    except Exception as e:
        return jsonify({
            "ok": False,
            "version": "V42.2_GOLD_INSTITUTIONAL_ENTRY_FILTER_STABLE",
            "error": str(e),
        }), 200


@v42_gold_bp.route("/v42/gold-text", methods=["GET"])
def v42_gold_text():
    try:
        from modules.v42_gold_institutional_core import build_v42_gold_text
        return Response(build_v42_gold_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึงระบบ V42 GOLD ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


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
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "version": "V42.2_GOLD_INSTITUTIONAL_ENTRY_FILTER_STABLE",
            "error": str(e),
        }), 200


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
            "engine": payload.get("engine"),
            "trade_plan": payload.get("trade_plan"),
            "push_alert": payload.get("push_alert"),
        })
    except Exception as e:
        return jsonify({"ok": False, "version": "V42.2_GOLD_INSTITUTIONAL_ENTRY_FILTER_STABLE", "error": str(e)}), 200
