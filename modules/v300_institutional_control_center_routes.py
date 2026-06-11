
from flask import Blueprint, jsonify, Response, request

v300_bp = Blueprint("v300_institutional_control_center", __name__)

@v300_bp.route("/v300/control-center", methods=["GET"])
def v300_control_center_text():
    try:
        from modules.v300_institutional_control_center.control_center import control_center_text
        return Response(control_center_text(request.args.get("symbol","SPY").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V300 Control Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v300_bp.route("/v300/control-center-json", methods=["GET"])
def v300_control_center_json():
    try:
        from modules.v300_institutional_control_center.control_center import institutional_control_center
        return jsonify(institutional_control_center(request.args.get("symbol","SPY").upper()))
    except Exception as e:
        return jsonify({"ok": False, "version": "V300_INSTITUTIONAL_CONTROL_CENTER_STABLE", "error": str(e)}), 200

@v300_bp.route("/v300/data-bus", methods=["GET"])
def v300_data_bus():
    try:
        from modules.v300_institutional_control_center.data_bus import data_bus_status
        return jsonify(data_bus_status())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v300_bp.route("/v300/feature-store", methods=["GET"])
def v300_feature_store():
    try:
        from modules.v300_institutional_control_center.feature_store import feature_store_status
        return jsonify(feature_store_status())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v300_bp.route("/v300/model-registry", methods=["GET"])
def v300_model_registry():
    try:
        from modules.v300_institutional_control_center.model_registry import model_registry_status
        return jsonify(model_registry_status())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v300_bp.route("/v300/explain", methods=["GET"])
def v300_explain():
    try:
        from modules.v300_institutional_control_center.explainability import explain_decision
        return jsonify(explain_decision(request.args.get("symbol","SPY").upper(), request.args.get("decision","WAIT")))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v300_bp.route("/v300/compatibility", methods=["GET"])
def v300_compatibility():
    try:
        from modules.v300_institutional_control_center.compatibility import compatibility_report
        return jsonify(compatibility_report())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
