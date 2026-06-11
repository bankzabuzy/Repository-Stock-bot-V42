
from flask import Blueprint, jsonify, Response, request

v220_bp = Blueprint("v220_broker_execution_network", __name__)

@v220_bp.route("/v220/broker-network", methods=["GET"])
def v220_broker_network_text():
    try:
        from modules.v220_broker_execution_network.dashboard import build_v220_text
        symbol = request.args.get("symbol", "SPY").upper()
        return Response(build_v220_text(symbol), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V220 Broker Network ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v220_bp.route("/v220/broker-network-json", methods=["GET"])
def v220_broker_network_json():
    try:
        from modules.v220_broker_execution_network.dashboard import build_v220_payload
        symbol = request.args.get("symbol", "SPY").upper()
        return jsonify(build_v220_payload(symbol))
    except Exception as e:
        return jsonify({"ok": False, "version": "V220_BROKER_EXECUTION_NETWORK_COMPATIBILITY_STABLE", "error": str(e)}), 200

@v220_bp.route("/v220/route-test", methods=["GET"])
def v220_route_test():
    try:
        from modules.v220_broker_execution_network.pretrade_router import route_execution
        return jsonify(route_execution(
            request.args.get("symbol", "SPY").upper(),
            request.args.get("side", "BUY").upper(),
            request.args.get("qty", "1"),
            request.args.get("price", "100"),
            request.args.get("broker", "PAPER").upper(),
            request.args.get("mode", "PAPER").upper(),
        ))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v220_bp.route("/v220/compatibility", methods=["GET"])
def v220_compatibility():
    try:
        from modules.v220_broker_execution_network.compatibility import compatibility_report
        return jsonify(compatibility_report(True))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
