
from flask import Blueprint, jsonify, Response, request

v620_bp = Blueprint("v620_phase6_alpha_discovery_engine", __name__)

@v620_bp.route("/v620/alpha-discovery", methods=["GET"])
def v620_alpha_discovery_text():
    try:
        from modules.v620_phase6_alpha_discovery_engine.engine import center_text
        return Response(center_text(request.args.get("symbol", "SPY").upper(), request.args.get("regime", "MIXED").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V620 Alpha Discovery ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v620_bp.route("/v620/alpha-discovery-json", methods=["GET"])
def v620_alpha_discovery_json():
    from modules.v620_phase6_alpha_discovery_engine.engine import center
    return jsonify(center(request.args.get("symbol","SPY").upper(), request.args.get("regime","MIXED").upper()))

@v620_bp.route("/v620/alpha-factory", methods=["GET"])
def v620_alpha_factory():
    from modules.v620_phase6_alpha_discovery_engine.engine import alpha_factory
    return jsonify(alpha_factory(request.args.get("symbol","SPY").upper()))

@v620_bp.route("/v620/factors", methods=["GET"])
def v620_factors():
    from modules.v620_phase6_alpha_discovery_engine.engine import factor_engine
    return jsonify(factor_engine(request.args.get("symbol","SPY").upper()))

@v620_bp.route("/v620/attribution", methods=["GET"])
def v620_attribution():
    from modules.v620_phase6_alpha_discovery_engine.engine import strategy_attribution
    return jsonify(strategy_attribution())

@v620_bp.route("/v620/decay", methods=["GET"])
def v620_decay():
    from modules.v620_phase6_alpha_discovery_engine.engine import alpha_decay
    return jsonify(alpha_decay())

@v620_bp.route("/v620/ensemble", methods=["GET"])
def v620_ensemble():
    from modules.v620_phase6_alpha_discovery_engine.engine import dynamic_ensemble
    return jsonify(dynamic_ensemble(request.args.get("regime","MIXED").upper()))

@v620_bp.route("/v620/rotation", methods=["GET"])
def v620_rotation():
    from modules.v620_phase6_alpha_discovery_engine.engine import regime_rotation
    return jsonify(regime_rotation(request.args.get("regime","MIXED").upper()))

@v620_bp.route("/v620/research", methods=["GET"])
def v620_research():
    from modules.v620_phase6_alpha_discovery_engine.engine import research_notebook
    return jsonify(research_notebook(request.args.get("symbol","SPY").upper(), request.args.get("alpha","Momentum")))
