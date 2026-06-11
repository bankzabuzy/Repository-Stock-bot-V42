
from flask import Blueprint, jsonify, Response, request

v200_bp = Blueprint("v200_autonomous_retail_fund", __name__)

@v200_bp.route("/v200/fund-manager", methods=["GET"])
def v200_fund_manager_text():
    try:
        from modules.v200_autonomous_retail_fund.dashboard import build_v200_text
        symbol = request.args.get("symbol", "SPY").upper()
        return Response(build_v200_text(symbol), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V200 Fund Manager ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v200_bp.route("/v200/fund-manager-json", methods=["GET"])
def v200_fund_manager_json():
    try:
        from modules.v200_autonomous_retail_fund.dashboard import build_v200_payload
        symbol = request.args.get("symbol", "SPY").upper()
        return jsonify(build_v200_payload(symbol))
    except Exception as e:
        return jsonify({"ok": False, "version": "V200_AUTONOMOUS_RETAIL_FUND_PLATFORM_STABLE", "error": str(e)}), 200

@v200_bp.route("/v200/human-error", methods=["GET"])
def v200_human_error():
    try:
        from modules.v200_autonomous_retail_fund.human_error_protection import human_error_protection
        return jsonify(human_error_protection(dict(request.args)))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v200_bp.route("/v200/kill-switch", methods=["GET"])
def v200_kill_switch():
    try:
        from modules.v200_autonomous_retail_fund.kill_switch_shadow_alerts import emergency_kill_switch
        return jsonify(emergency_kill_switch(request.args.get("symbol","SPY").upper()))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v200_bp.route("/v200/line-alert-test", methods=["GET"])
def v200_line_alert_test():
    try:
        from modules.v200_autonomous_retail_fund.kill_switch_shadow_alerts import institutional_line_alert
        return jsonify(institutional_line_alert("V200 TEST ALERT", 90, 88, "A", 2.5, dict(request.args)))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v200_bp.route("/v200/audit", methods=["GET"])
def v200_audit_route():
    try:
        from modules.v200_autonomous_retail_fund.audit import v200_audit
        return jsonify(v200_audit())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
