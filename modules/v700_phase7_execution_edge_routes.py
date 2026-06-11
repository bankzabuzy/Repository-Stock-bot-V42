
from flask import Blueprint, jsonify, Response, request

v700_bp = Blueprint("v700_phase7_execution_edge", __name__)

@v700_bp.route("/v700/execution-edge", methods=["GET"])
def v700_execution_edge_text():
    try:
        from modules.v700_phase7_execution_edge.core import dashboard_text
        return Response(dashboard_text(request.args.get("symbol", "SPY").upper(), request.args.get("regime", "MIXED").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V700 Execution Edge ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v700_bp.route("/v700/execution-edge-json", methods=["GET"])
def v700_execution_edge_json():
    from modules.v700_phase7_execution_edge.core import dashboard
    return jsonify(dashboard(request.args.get("symbol", "SPY").upper(), request.args.get("regime", "MIXED").upper()))

@v700_bp.route("/v700/position-sizing", methods=["GET"])
def v700_position_sizing():
    from modules.v700_phase7_execution_edge.core import position_sizing
    return jsonify(position_sizing(request.args.get("symbol","SPY").upper(), request.args.get("grade","A").upper(), request.args.get("confidence","85")))

@v700_bp.route("/v700/kelly", methods=["GET"])
def v700_kelly():
    from modules.v700_phase7_execution_edge.core import kelly
    return jsonify(kelly(request.args.get("symbol","SPY").upper(), request.args.get("winrate","0.55"), request.args.get("payoff","1.6")))

@v700_bp.route("/v700/heat", methods=["GET"])
def v700_heat():
    from modules.v700_phase7_execution_edge.core import portfolio_heat
    return jsonify(portfolio_heat())

@v700_bp.route("/v700/exposure", methods=["GET"])
def v700_exposure():
    from modules.v700_phase7_execution_edge.core import exposure
    return jsonify(exposure())

@v700_bp.route("/v700/correlation", methods=["GET"])
def v700_correlation():
    from modules.v700_phase7_execution_edge.core import correlation
    return jsonify(correlation())

@v700_bp.route("/v700/risk-control", methods=["GET"])
def v700_risk_control():
    from modules.v700_phase7_execution_edge.core import concentration, exposure, correlation, portfolio_heat
    return jsonify({"concentration": concentration(), "exposure": exposure(), "correlation": correlation(), "heat": portfolio_heat()})
