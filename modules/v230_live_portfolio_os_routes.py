
from flask import Blueprint, jsonify, Response

v230_bp = Blueprint("v230_live_portfolio_os", __name__)

@v230_bp.route("/v230/portfolio-os", methods=["GET"])
def v230_portfolio_os_text():
    try:
        from modules.v230_live_portfolio_os.dashboard import build_v230_text
        return Response(build_v230_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V230 Portfolio OS ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v230_bp.route("/v230/portfolio-os-json", methods=["GET"])
def v230_portfolio_os_json():
    try:
        from modules.v230_live_portfolio_os.dashboard import build_v230_payload
        return jsonify(build_v230_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V230_LIVE_PORTFOLIO_OS_STABLE", "error": str(e)}), 200

@v230_bp.route("/v230/rebalance", methods=["GET"])
def v230_rebalance():
    try:
        from modules.v230_live_portfolio_os.rebalance_engine import rebalance_plan
        return jsonify(rebalance_plan())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v230_bp.route("/v230/compatibility", methods=["GET"])
def v230_compatibility():
    try:
        from modules.v230_live_portfolio_os.compatibility import compatibility_report
        return jsonify(compatibility_report(True))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
