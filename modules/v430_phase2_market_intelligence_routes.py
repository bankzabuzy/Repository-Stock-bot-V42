
from flask import Blueprint, jsonify, Response, request

v430_bp = Blueprint("v430_phase2_market_intelligence", __name__)

@v430_bp.route("/v430/phase2-center", methods=["GET"])
def v430_phase2_center_text():
    try:
        from modules.v430_phase2_market_intelligence.dashboard import phase2_text
        return Response(phase2_text(request.args.get("symbol", "SPY").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V430 Phase 2 Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v430_bp.route("/v430/phase2-center-json", methods=["GET"])
def v430_phase2_center_json():
    from modules.v430_phase2_market_intelligence.dashboard import phase2_center
    return jsonify(phase2_center(request.args.get("symbol", "SPY").upper()))

@v430_bp.route("/v430/microstructure", methods=["GET"])
def v430_microstructure():
    from modules.v430_phase2_market_intelligence.microstructure_ai import market_microstructure
    return jsonify(market_microstructure(request.args.get("symbol","SPY").upper()))

@v430_bp.route("/v430/regime", methods=["GET"])
def v430_regime():
    from modules.v430_phase2_market_intelligence.regime_ai import regime_ai
    return jsonify(regime_ai(request.args.get("symbol","SPY").upper()))

@v430_bp.route("/v430/debate", methods=["GET"])
def v430_debate():
    from modules.v430_phase2_market_intelligence.multi_agent_debate import multi_agent_debate
    return jsonify(multi_agent_debate(request.args.get("symbol","SPY").upper()))

@v430_bp.route("/v430/digital-twin", methods=["GET"])
def v430_digital_twin():
    from modules.v430_phase2_market_intelligence.digital_twin import digital_twin_gate
    return jsonify(digital_twin_gate(request.args.get("symbol","SPY").upper()))
