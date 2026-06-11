
from flask import Blueprint, jsonify, Response, request

v51_bp = Blueprint("v51_validation_execution", __name__)


@v51_bp.route("/v51/validation", methods=["GET"])
def v51_validation_json():
    try:
        from modules.v51_institutional_validation_execution import build_v51_payload
        symbol = request.args.get("symbol", "SPY").upper()
        return jsonify(build_v51_payload(symbol))
    except Exception as e:
        return jsonify({"ok": False, "version": "V51_INSTITUTIONAL_VALIDATION_AND_EXECUTION_PROOF_STABLE", "error": str(e)}), 200


@v51_bp.route("/v51/dashboard", methods=["GET"])
def v51_dashboard_text():
    try:
        from modules.v51_institutional_validation_execution import build_v51_dashboard_text
        symbol = request.args.get("symbol", "SPY").upper()
        return Response(build_v51_dashboard_text(symbol), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V51 Dashboard ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


@v51_bp.route("/v51/paper-order", methods=["GET"])
def v51_paper_order():
    try:
        from modules.v51_institutional_validation_execution import paper_broker_order
        symbol = request.args.get("symbol", "SPY").upper()
        side = request.args.get("side", "BUY").upper()
        qty = float(request.args.get("qty", "1"))
        entry = request.args.get("entry")
        tp = request.args.get("tp")
        sl = request.args.get("sl")
        return jsonify(paper_broker_order(symbol, side, qty, entry, tp, sl))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v51_bp.route("/v51/kill-switch", methods=["GET"])
def v51_kill_switch():
    try:
        from modules.v51_institutional_validation_execution import kill_switch
        return jsonify(kill_switch())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v51_bp.route("/v51/calibration", methods=["GET"])
def v51_calibration():
    try:
        from modules.v51_institutional_validation_execution import calibration_curve
        return jsonify(calibration_curve())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v51_bp.route("/v51/exposure", methods=["GET"])
def v51_exposure():
    try:
        from modules.v51_institutional_validation_execution import portfolio_exposure
        return jsonify(portfolio_exposure())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
