
from flask import Blueprint, jsonify, Response, request

v470_bp = Blueprint("v470_phase3_meta_selfheal_dashboard", __name__)

@v470_bp.route("/v470/phase3-center", methods=["GET"])
def v470_phase3_center_text():
    try:
        from modules.v470_phase3_meta_selfheal_dashboard.dashboard import phase3_text
        return Response(phase3_text(request.args.get("symbol", "SPY").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V470 Phase 3 Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v470_bp.route("/v470/phase3-center-json", methods=["GET"])
def v470_phase3_center_json():
    from modules.v470_phase3_meta_selfheal_dashboard.dashboard import phase3_center
    return jsonify(phase3_center(request.args.get("symbol", "SPY").upper()))

@v470_bp.route("/v470/meta-learning", methods=["GET"])
def v470_meta_learning():
    from modules.v470_phase3_meta_selfheal_dashboard.meta_learning import meta_learning_weights
    return jsonify(meta_learning_weights())

@v470_bp.route("/v470/self-healing", methods=["GET"])
def v470_self_healing():
    from modules.v470_phase3_meta_selfheal_dashboard.self_healing import self_healing_check
    return jsonify(self_healing_check())

@v470_bp.route("/v470/explainable-report", methods=["GET"])
def v470_explainable_report():
    from modules.v470_phase3_meta_selfheal_dashboard.explainable_fund_report import explainable_fund_report
    return jsonify(explainable_fund_report(request.args.get("symbol","SPY").upper()))

@v470_bp.route("/v470/investor-dashboard", methods=["GET"])
def v470_investor_dashboard():
    from modules.v470_phase3_meta_selfheal_dashboard.investor_dashboard import investor_dashboard
    return jsonify(investor_dashboard())
