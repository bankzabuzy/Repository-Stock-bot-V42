
from flask import Blueprint, jsonify, Response, request

v210_bp = Blueprint("v210_multi_agent_fund_intelligence", __name__)

@v210_bp.route("/v210/agent-center", methods=["GET"])
def v210_agent_center_text():
    try:
        from modules.v210_multi_agent_fund_intelligence.dashboard import build_v210_text
        symbol = request.args.get("symbol", "SPY").upper()
        return Response(build_v210_text(symbol), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V210 Agent Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v210_bp.route("/v210/agent-center-json", methods=["GET"])
def v210_agent_center_json():
    try:
        from modules.v210_multi_agent_fund_intelligence.dashboard import build_v210_payload
        symbol = request.args.get("symbol", "SPY").upper()
        return jsonify(build_v210_payload(symbol))
    except Exception as e:
        return jsonify({"ok": False, "version": "V210_MULTI_AGENT_FUND_INTELLIGENCE_STABLE", "error": str(e)}), 200

@v210_bp.route("/v210/agents", methods=["GET"])
def v210_agents():
    try:
        from modules.v210_multi_agent_fund_intelligence.agents import run_agents
        symbol = request.args.get("symbol", "SPY").upper()
        return jsonify(run_agents(symbol))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v210_bp.route("/v210/compatibility", methods=["GET"])
def v210_compatibility():
    try:
        from modules.v210_multi_agent_fund_intelligence.compatibility import compatibility_report
        return jsonify(compatibility_report(True))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
