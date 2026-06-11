
from flask import Blueprint, jsonify, Response, request

v130_bp = Blueprint("v130_live_readiness_autonomous", __name__)

@v130_bp.route("/v130/governance-center", methods=["GET"])
def v130_governance_text():
    try:
        from modules.v130_live_readiness_autonomous.governance_report import build_v130_text
        return Response(build_v130_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V130 Governance Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v130_bp.route("/v130/governance-json", methods=["GET"])
def v130_governance_json():
    try:
        from modules.v130_live_readiness_autonomous.governance_report import build_v130_payload
        return jsonify(build_v130_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V130_LIVE_TRADING_READINESS_AUTONOMOUS_PORTFOLIO_CONTROL_STABLE", "error": str(e)}), 200

@v130_bp.route("/v130/readiness", methods=["GET"])
def v130_readiness():
    try:
        from modules.v130_live_readiness_autonomous.readiness import run_readiness_checks
        return jsonify(run_readiness_checks())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v130_bp.route("/v130/allocation", methods=["GET"])
def v130_allocation():
    try:
        from modules.v130_live_readiness_autonomous.capital_allocation import allocation_plan
        return jsonify(allocation_plan())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v130_bp.route("/v130/autonomous-rebalance", methods=["GET"])
def v130_autonomous_rebalance():
    try:
        from modules.v130_live_readiness_autonomous.autonomous_controls import generate_rebalance_intents
        return jsonify(generate_rebalance_intents())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v130_bp.route("/v130/incidents", methods=["GET"])
def v130_incidents():
    try:
        from modules.v130_live_readiness_autonomous.incident_response import incident_summary
        return jsonify(incident_summary())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
