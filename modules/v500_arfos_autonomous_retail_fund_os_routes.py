
from flask import Blueprint, jsonify, Response, request

v500_bp = Blueprint("v500_arfos_autonomous_retail_fund_os", __name__)

@v500_bp.route("/v500/arfos", methods=["GET"])
def v500_arfos_text():
    try:
        from modules.v500_arfos_autonomous_retail_fund_os.dashboard import phase4_text
        return Response(phase4_text(request.args.get("symbol", "SPY").upper()), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V500 ARFOS ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v500_bp.route("/v500/arfos-json", methods=["GET"])
def v500_arfos_json():
    from modules.v500_arfos_autonomous_retail_fund_os.dashboard import phase4_center
    return jsonify(phase4_center(request.args.get("symbol", "SPY").upper()))

@v500_bp.route("/v500/shadow", methods=["GET"])
def v500_shadow():
    from modules.v500_arfos_autonomous_retail_fund_os.shadow_real_money import shadow_real_money
    return jsonify(shadow_real_money(request.args.get("symbol", "SPY").upper(), request.args.get("human_decision", "WAIT").upper()))

@v500_bp.route("/v500/governance", methods=["GET"])
def v500_governance():
    from modules.v500_arfos_autonomous_retail_fund_os.autonomous_governance import governance_status
    return jsonify(governance_status())

@v500_bp.route("/v500/compatibility", methods=["GET"])
def v500_compatibility():
    from modules.v500_arfos_autonomous_retail_fund_os.arfos_core import compatibility_audit
    return jsonify(compatibility_audit())
