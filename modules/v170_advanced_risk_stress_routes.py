
from flask import Blueprint, jsonify, Response, request

v170_bp = Blueprint("v170_advanced_risk_stress", __name__)

@v170_bp.route("/v170/risk-center", methods=["GET"])
def v170_risk_center_text():
    try:
        from modules.v170_advanced_risk_stress.risk_dashboard import build_v170_text
        return Response(build_v170_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V170 Risk Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v170_bp.route("/v170/risk-center-json", methods=["GET"])
def v170_risk_center_json():
    try:
        from modules.v170_advanced_risk_stress.risk_dashboard import build_v170_payload
        return jsonify(build_v170_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V170_ADVANCED_RISK_AND_STRESS_TESTING_STABLE", "error": str(e)}), 200

@v170_bp.route("/v170/scenarios", methods=["GET"])
def v170_scenarios():
    try:
        from modules.v170_advanced_risk_stress.scenario_engine import run_all_scenarios
        return jsonify(run_all_scenarios())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v170_bp.route("/v170/monte-carlo", methods=["GET"])
def v170_monte_carlo():
    try:
        from modules.v170_advanced_risk_stress.monte_carlo import monte_carlo_stress
        trials = int(request.args.get("trials", "5000"))
        return jsonify(monte_carlo_stress(trials))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v170_bp.route("/v170/var-cvar", methods=["GET"])
def v170_var_cvar():
    try:
        from modules.v170_advanced_risk_stress.portfolio_risk import portfolio_var_cvar
        return jsonify(portfolio_var_cvar())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v170_bp.route("/v170/correlation", methods=["GET"])
def v170_corr():
    try:
        from modules.v170_advanced_risk_stress.portfolio_risk import correlation_matrix
        return jsonify(correlation_matrix())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
