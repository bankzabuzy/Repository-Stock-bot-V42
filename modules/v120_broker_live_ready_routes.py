
from flask import Blueprint, jsonify, Response, request

v120_bp = Blueprint("v120_broker_live_ready", __name__)

@v120_bp.route("/v120/broker-center", methods=["GET"])
def v120_broker_center_text():
    try:
        from modules.v120_broker_live_ready.broker_dashboard import build_v120_text
        return Response(build_v120_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V120 Broker Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v120_bp.route("/v120/broker-center-json", methods=["GET"])
def v120_broker_center_json():
    try:
        from modules.v120_broker_live_ready.broker_dashboard import build_v120_payload
        return jsonify(build_v120_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V120_BROKER_LIVE_READY_SAFETY_LAYER_STABLE", "error": str(e)}), 200

@v120_bp.route("/v120/brokers", methods=["GET"])
def v120_brokers():
    try:
        from modules.v120_broker_live_ready.broker_adapters import all_broker_status
        return jsonify(all_broker_status())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v120_bp.route("/v120/order-test", methods=["GET"])
def v120_order_test():
    try:
        from modules.v120_broker_live_ready.order_router import create_and_route
        symbol = request.args.get("symbol", "SPY")
        side = request.args.get("side", "BUY")
        qty = request.args.get("qty", "1")
        broker = request.args.get("broker", "PAPER")
        mode = request.args.get("mode", "PAPER")
        price = request.args.get("price", "500")
        return jsonify(create_and_route(symbol, side, qty, broker, mode, price))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v120_bp.route("/v120/portfolio", methods=["GET"])
def v120_portfolio():
    try:
        from modules.v120_broker_live_ready.portfolio_sync import portfolio_snapshot
        return jsonify(portfolio_snapshot())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
