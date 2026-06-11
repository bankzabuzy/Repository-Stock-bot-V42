
from flask import Blueprint, jsonify, Response, request

v110_bp = Blueprint("v110_retail_institutional_fund", __name__)

@v110_bp.route("/fund", methods=["GET"])
def fund_text():
    try:
        from modules.v110_retail_institutional_fund.master_dashboard import build_master_text
        return Response(build_master_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง Fund Dashboard ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v110_bp.route("/fund-json", methods=["GET"])
def fund_json():
    try:
        from modules.v110_retail_institutional_fund.master_dashboard import build_master_payload
        return jsonify(build_master_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V110_RETAIL_INSTITUTIONAL_FUND_PLATFORM_STABLE", "error": str(e)}), 200

@v110_bp.route("/v110/daily-report", methods=["GET"])
def v110_daily_report():
    try:
        from modules.v110_retail_institutional_fund.daily_report import save_daily_report
        data = save_daily_report()
        return Response(data.get("report_text", str(data)), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถสร้าง Daily Fund Report ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")

@v110_bp.route("/v110/execution-sim", methods=["GET"])
def v110_execution_sim():
    try:
        from modules.v110_retail_institutional_fund.execution_simulator import simulate_execution
        symbol = request.args.get("symbol", "SPY")
        side = request.args.get("side", "BUY")
        price = request.args.get("price", "100")
        qty = request.args.get("qty", "1")
        return jsonify(simulate_execution(symbol, side, price, qty))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v110_bp.route("/v110/data-quality", methods=["GET"])
def v110_data_quality():
    try:
        from modules.v110_retail_institutional_fund.data_quality import check_data_sources
        symbols = request.args.get("symbols", "")
        items = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None
        return jsonify(check_data_sources(items))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v110_bp.route("/v110/model-registry", methods=["GET"])
def v110_model_registry():
    try:
        from modules.v110_retail_institutional_fund.model_registry import registry
        return jsonify(registry())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v110_bp.route("/v110/strategy-ranking", methods=["GET"])
def v110_strategy_ranking():
    try:
        from modules.v110_retail_institutional_fund.strategy_ranking import strategy_ranking
        return jsonify(strategy_ranking())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v110_bp.route("/v110/regime", methods=["GET"])
def v110_regime():
    try:
        from modules.v110_retail_institutional_fund.regime_engine import market_regime
        return jsonify(market_regime())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v110_bp.route("/v110/exposure", methods=["GET"])
def v110_exposure():
    try:
        from modules.v110_retail_institutional_fund.exposure_control import exposure_control
        return jsonify(exposure_control())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

@v110_bp.route("/v110/shadow-portfolios", methods=["GET"])
def v110_shadow():
    try:
        from modules.v110_retail_institutional_fund.shadow_portfolio import shadow_summary
        return jsonify(shadow_summary())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
