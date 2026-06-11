
from flask import Blueprint, jsonify, Response, request

v240_bp = Blueprint("v240_autonomous_fund_manager", __name__)

@v240_bp.route("/v240/fund-manager", methods=["GET"])
def v240_fund_manager_text():
    try:
        from modules.v240_autonomous_fund_manager.dashboard import build_v240_text
        return Response(build_v240_text(request.args.get("symbol", "SPY").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V240 Fund Manager ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v240_bp.route("/v240/fund-manager-json", methods=["GET"])
def v240_fund_manager_json():
    try:
        from modules.v240_autonomous_fund_manager.dashboard import build_v240_payload
        return jsonify(build_v240_payload(request.args.get("symbol", "SPY").upper()))
    except Exception as e:
        return jsonify({"ok": False, "version": "V240_AUTONOMOUS_FUND_MANAGER_STABLE", "error": str(e)}), 200

@v240_bp.route("/v240/health", methods=["GET"])
def v240_health():
    try:
        from modules.v240_autonomous_fund_manager.fund_health_auto_pause import fund_health_score
        return jsonify(fund_health_score())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v240_bp.route("/v240/watchlist", methods=["GET"])
def v240_watchlist():
    try:
        from modules.v240_autonomous_fund_manager.watchlist_journal import watchlist_rank
        return jsonify(watchlist_rank())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v240_bp.route("/v240/compatibility", methods=["GET"])
def v240_compatibility():
    try:
        from modules.v240_autonomous_fund_manager.compatibility import compatibility_report
        return jsonify(compatibility_report(True))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
