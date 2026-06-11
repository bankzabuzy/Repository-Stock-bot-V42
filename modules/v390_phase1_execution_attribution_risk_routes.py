
from flask import Blueprint, jsonify, Response, request

v390_bp = Blueprint("v390_phase1_execution_attribution_risk", __name__)

@v390_bp.route("/v390/phase1-center", methods=["GET"])
def v390_phase1_center_text():
    try:
        from modules.v390_phase1_execution_attribution_risk.dashboard import phase1_text
        return Response(phase1_text(request.args.get("symbol", "SPY").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V390 Phase 1 Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v390_bp.route("/v390/phase1-center-json", methods=["GET"])
def v390_phase1_center_json():
    try:
        from modules.v390_phase1_execution_attribution_risk.dashboard import phase1_center
        return jsonify(phase1_center(request.args.get("symbol", "SPY").upper()))
    except Exception as e:
        return jsonify({"ok": False, "version": "V390_PHASE1_EXECUTION_ATTRIBUTION_RISK_STABLE", "error": str(e)}), 200

@v390_bp.route("/v390/execution-verification", methods=["GET"])
def v390_execution_verification():
    from modules.v390_phase1_execution_attribution_risk.execution_verification import execution_verification_status
    return jsonify(execution_verification_status())

@v390_bp.route("/v390/attribution", methods=["GET"])
def v390_attribution():
    from modules.v390_phase1_execution_attribution_risk.attribution_engine import attribution_report
    return jsonify(attribution_report())

@v390_bp.route("/v390/position-sizing", methods=["GET"])
def v390_position_sizing():
    from modules.v390_phase1_execution_attribution_risk.position_sizing_ai import position_sizing
    return jsonify(position_sizing(request.args.get("symbol","SPY").upper()))

@v390_bp.route("/v390/capital-protection", methods=["GET"])
def v390_capital_protection():
    from modules.v390_phase1_execution_attribution_risk.capital_protection import capital_protection
    return jsonify(capital_protection(
        request.args.get("drawdown","0"),
        request.args.get("losing_days","0"),
        request.args.get("profit_factor","1.2"),
        request.args.get("volatility_level","NORMAL"),
    ))
