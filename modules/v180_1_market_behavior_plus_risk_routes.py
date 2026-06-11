
from flask import Blueprint, jsonify, Response

v180_1_bp = Blueprint("v180_1_market_behavior_plus_risk", __name__)

@v180_1_bp.route("/v180-1/forecast", methods=["GET"])
def v180_1_forecast_text():
    try:
        from modules.v180_1_market_behavior_plus_risk.forecast_plus_risk import forecast_text, save_audit
        from modules.v180_1_market_behavior_plus_risk.audit import route_collision_audit
        rc = route_collision_audit()
        save_audit(True, rc.get("collision_count", 0))
        return Response(forecast_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V180.1 Forecast ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v180_1_bp.route("/v180-1/forecast-json", methods=["GET"])
def v180_1_forecast_json():
    try:
        from modules.v180_1_market_behavior_plus_risk.forecast_plus_risk import forecast_decision, save_audit
        from modules.v180_1_market_behavior_plus_risk.audit import route_collision_audit
        rc = route_collision_audit()
        save_audit(True, rc.get("collision_count", 0))
        return jsonify(forecast_decision())
    except Exception as e:
        return jsonify({"ok": False, "version": "V180.1_MARKET_BEHAVIOR_FORECAST_PLUS_RISK_STRESS_BASE_STABLE", "error": str(e)}), 200

@v180_1_bp.route("/v180-1/audit", methods=["GET"])
def v180_1_audit():
    try:
        from modules.v180_1_market_behavior_plus_risk.audit import full_audit
        return jsonify(full_audit())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
