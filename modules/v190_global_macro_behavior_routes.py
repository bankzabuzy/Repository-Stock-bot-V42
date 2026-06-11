
from flask import Blueprint, jsonify, Response

v190_bp = Blueprint("v190_global_macro_behavior", __name__)

@v190_bp.route("/v190/macro-center", methods=["GET"])
def v190_macro_center_text():
    try:
        from modules.v190_global_macro_behavior.dashboard import build_v190_text
        return Response(build_v190_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V190 Macro Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v190_bp.route("/v190/macro-center-json", methods=["GET"])
def v190_macro_center_json():
    try:
        from modules.v190_global_macro_behavior.dashboard import build_v190_payload
        return jsonify(build_v190_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V190_GLOBAL_MACRO_BEHAVIOR_AND_EVENT_PREDICTION_ENGINE_STABLE", "error": str(e)}), 200

@v190_bp.route("/v190/probability", methods=["GET"])
def v190_probability():
    try:
        from modules.v190_global_macro_behavior.probability_engine import probability_engine
        return jsonify(probability_engine())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v190_bp.route("/v190/events", methods=["GET"])
def v190_events():
    try:
        from modules.v190_global_macro_behavior.event_prediction import event_prediction
        return jsonify(event_prediction())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v190_bp.route("/v190/consensus", methods=["GET"])
def v190_consensus():
    try:
        from modules.v190_global_macro_behavior.consensus_factcheck import fact_check_layer
        return jsonify(fact_check_layer())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v190_bp.route("/v190/audit", methods=["GET"])
def v190_audit_route():
    try:
        from modules.v190_global_macro_behavior.audit import v190_audit
        return jsonify(v190_audit())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
