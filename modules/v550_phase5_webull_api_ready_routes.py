
from flask import Blueprint, jsonify, Response, request

v550_bp = Blueprint("v550_phase5_webull_api_ready", __name__)

@v550_bp.route("/v550/phase5-center", methods=["GET"])
def v550_phase5_center_text():
    try:
        from modules.v550_phase5_webull_api_ready.dashboard import phase5_text
        return Response(phase5_text(request.args.get("symbol", "SPY").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V550 Phase 5 Center ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v550_bp.route("/v550/phase5-center-json", methods=["GET"])
def v550_phase5_center_json():
    from modules.v550_phase5_webull_api_ready.dashboard import phase5_center
    return jsonify(phase5_center(request.args.get("symbol", "SPY").upper()))

@v550_bp.route("/v550/secrets", methods=["GET"])
def v550_secrets():
    from modules.v550_phase5_webull_api_ready.secret_manager import secret_manager_status
    return jsonify(secret_manager_status())

@v550_bp.route("/v550/brokers", methods=["GET"])
def v550_brokers():
    from modules.v550_phase5_webull_api_ready.broker_integration import broker_integration_status
    return jsonify(broker_integration_status())

@v550_bp.route("/v550/dry-run", methods=["GET"])
def v550_dry_run():
    from modules.v550_phase5_webull_api_ready.order_dryrun import order_dry_run
    return jsonify(order_dry_run(request.args.get("symbol","SPY").upper(), request.args.get("side","BUY").upper(), request.args.get("qty","1"), request.args.get("broker","WEBULL").upper()))

@v550_bp.route("/v550/approval", methods=["GET"])
def v550_approval():
    from modules.v550_phase5_webull_api_ready.human_approval import create_approval
    return jsonify(create_approval(request.args.get("symbol","SPY").upper(), request.args.get("side","BUY").upper(), request.args.get("qty","1"), request.args.get("broker","WEBULL").upper(), request.args.get("mode","SAFE").upper()))

@v550_bp.route("/v550/api-health", methods=["GET"])
def v550_api_health():
    from modules.v550_phase5_webull_api_ready.api_health_center import api_health_center
    return jsonify(api_health_center())

@v550_bp.route("/v550/safety", methods=["GET"])
def v550_safety():
    from modules.v550_phase5_webull_api_ready.safety_center import safety_center_status
    return jsonify(safety_center_status())
