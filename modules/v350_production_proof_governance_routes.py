
from flask import Blueprint, jsonify, Response, request
v350_bp=Blueprint("v350_production_proof_governance",__name__)
@v350_bp.route("/v350/production-center",methods=["GET"])
def v350_production_center_text():
    try:
        from modules.v350_production_proof_governance.production_control import production_center_text
        return Response(production_center_text(),mimetype="text/plain; charset=utf-8")
    except Exception as e: return Response(f"ไม่สามารถดึง V350 Production Center ได้ในขณะนี้: {e}",mimetype="text/plain; charset=utf-8")
@v350_bp.route("/v350/production-center-json",methods=["GET"])
def v350_production_center_json():
    try:
        from modules.v350_production_proof_governance.production_control import production_center
        return jsonify(production_center())
    except Exception as e: return jsonify({"ok":False,"version":"V350_PRODUCTION_PROOF_AND_GOVERNANCE_STABLE","error":str(e)}),200
@v350_bp.route("/v350/routes",methods=["GET"])
def v350_routes():
    from modules.v350_production_proof_governance.route_cleanup import route_cleanup_registry
    return jsonify(route_cleanup_registry())
@v350_bp.route("/v350/providers",methods=["GET"])
def v350_providers():
    from modules.v350_production_proof_governance.data_providers import provider_layer_status
    return jsonify(provider_layer_status())
@v350_bp.route("/v350/forward-test",methods=["GET"])
def v350_forward_test():
    from modules.v350_production_proof_governance.forward_test import forward_test_status, create_forward_signal
    symbol=request.args.get("symbol")
    return jsonify(create_forward_signal(symbol.upper(),request.args.get("side","BUY").upper(),int(request.args.get("horizon","30")))) if symbol else jsonify(forward_test_status())
@v350_bp.route("/v350/performance",methods=["GET"])
def v350_performance():
    from modules.v350_production_proof_governance.performance_proof import performance_dashboard
    return jsonify(performance_dashboard(int(request.args.get("window","90"))))
@v350_bp.route("/v350/line-governance",methods=["GET"])
def v350_line_governance():
    from modules.v350_production_proof_governance.line_governance import line_governance_status
    return jsonify(line_governance_status())
