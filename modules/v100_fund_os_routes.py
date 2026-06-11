
from flask import Blueprint, jsonify, Response, request

v100_bp = Blueprint("v100_fund_os", __name__)

@v100_bp.route("/v100/fund-os", methods=["GET"])
def v100_fund_os_json():
    try:
        from modules.v100_fund_os.fund_os import build_fund_os_payload
        symbol = request.args.get("symbol", "SPY").upper()
        return jsonify(build_fund_os_payload(symbol))
    except Exception as e:
        return jsonify({"ok": False, "version": "V100_FUND_OPERATING_SYSTEM_STABLE", "error": str(e)}), 200

@v100_bp.route("/v100/fund-dashboard", methods=["GET"])
def v100_fund_dashboard_text():
    try:
        from modules.v100_fund_os.fund_os import build_fund_dashboard_text
        symbol = request.args.get("symbol", "SPY").upper()
        return Response(build_fund_dashboard_text(symbol), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V100 Fund Dashboard ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v100_bp.route("/v100/health", methods=["GET"])
def v100_health_json():
    try:
        from modules.v100_fund_os.monitoring import health
        return jsonify(health())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v100_bp.route("/v100/research", methods=["GET"])
def v100_research_json():
    try:
        from modules.v100_fund_os.research import run_research_experiment
        name = request.args.get("name", "baseline_research")
        return jsonify(run_research_experiment(name))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
