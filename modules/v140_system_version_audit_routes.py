
from flask import Blueprint, jsonify, Response

v140_bp = Blueprint("v140_system_version_audit", __name__)

@v140_bp.route("/v140/system-center", methods=["GET"])
def v140_system_center_text():
    try:
        from modules.v140_system_version_audit.version_registry import latest_status_text, save_audit_record
        save_audit_record(True)
        return Response(latest_status_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V140 System Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v140_bp.route("/v140/system-center-json", methods=["GET"])
def v140_system_center_json():
    try:
        from modules.v140_system_version_audit.version_registry import latest_status_payload, save_audit_record
        save_audit_record(True)
        return jsonify(latest_status_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V140_SYSTEM_VERSION_CONSISTENCY_AUDIT_STABLE", "error": str(e)}), 200

@v140_bp.route("/v140/version-audit", methods=["GET"])
def v140_version_audit():
    try:
        from modules.v140_system_version_audit.version_registry import stale_reference_report
        return jsonify(stale_reference_report())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v140_bp.route("/v140/routes", methods=["GET"])
def v140_routes():
    try:
        from modules.v140_system_version_audit.version_registry import route_registry
        return jsonify(route_registry())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
