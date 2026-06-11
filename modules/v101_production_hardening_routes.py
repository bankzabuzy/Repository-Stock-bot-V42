
from flask import Blueprint, jsonify, Response, request

v101_bp = Blueprint("v101_production_hardening", __name__)

@v101_bp.route("/v101/production-center", methods=["GET"])
def v101_production_center():
    try:
        from modules.v101_production_hardening.monitoring import build_v101_text
        return Response(build_v101_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V101 Production Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v101_bp.route("/v101/production-center-json", methods=["GET"])
def v101_production_center_json():
    try:
        from modules.v101_production_hardening.monitoring import build_v101_payload
        return jsonify(build_v101_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V101_PRODUCTION_HARDENING_SECURITY_STABLE", "error": str(e)}), 200

@v101_bp.route("/v101/self-test", methods=["GET"])
def v101_self_test():
    try:
        from modules.v101_production_hardening.selftest import full_self_test
        return jsonify(full_self_test())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v101_bp.route("/v101/config", methods=["GET"])
def v101_config():
    try:
        from modules.v101_production_hardening.security import safe_public_config
        return jsonify(safe_public_config())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v101_bp.route("/v101/errors", methods=["GET"])
def v101_errors():
    try:
        from modules.v101_production_hardening.state import last_errors
        return jsonify(last_errors(20))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v101_bp.route("/v101/db-summary", methods=["GET"])
def v101_db_summary():
    try:
        from modules.v101_production_hardening.backup import db_summary
        return jsonify(db_summary())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v101_bp.route("/v101/maintenance", methods=["GET"])
def v101_maintenance():
    try:
        from modules.v101_production_hardening.security import verify_admin_token
        from modules.v101_production_hardening.state import set_state
        token = request.args.get("token")
        enabled = request.args.get("enabled", "false")
        auth = verify_admin_token(token)
        if not auth.get("ok"):
            return jsonify({"ok": False, "auth": auth}), 403
        return jsonify(set_state("maintenance_mode", enabled))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
