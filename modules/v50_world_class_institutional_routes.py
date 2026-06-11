
from flask import Blueprint, jsonify, Response, request

v50_bp = Blueprint("v50_world_class", __name__)


@v50_bp.route("/v50/world-class", methods=["GET"])
def v50_world_class_json():
    try:
        from modules.v50_world_class_institutional_stack import build_v50_world_class_payload
        return jsonify(build_v50_world_class_payload())
    except Exception as e:
        return jsonify({"ok": False, "version": "V50_WORLD_CLASS_INSTITUTIONAL_STACK_STABLE", "error": str(e)}), 200


@v50_bp.route("/v50/world-class-dashboard", methods=["GET"])
def v50_world_class_dashboard():
    try:
        from modules.v50_world_class_institutional_stack import build_v50_world_class_dashboard_text
        return Response(build_v50_world_class_dashboard_text(), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"ไม่สามารถดึง V50 World-Class Dashboard ได้ในขณะนี้: {e}", mimetype="text/plain; charset=utf-8")


@v50_bp.route("/v43/portfolio-manager", methods=["GET"])
def v43_portfolio_manager_json():
    try:
        from modules.v50_world_class_institutional_stack import v43_portfolio_manager
        return jsonify(v43_portfolio_manager())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v50_bp.route("/v44/relative-strength", methods=["GET"])
def v44_relative_strength_json():
    try:
        from modules.v50_world_class_institutional_stack import v44_relative_strength
        symbols_raw = request.args.get("symbols", "")
        symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()] if symbols_raw else None
        return jsonify(v44_relative_strength(symbols))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v50_bp.route("/v45/options-flow", methods=["GET"])
def v45_options_flow_json():
    try:
        from modules.v50_world_class_institutional_stack import v45_options_flow
        return jsonify(v45_options_flow())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v50_bp.route("/v46/dark-pool", methods=["GET"])
def v46_dark_pool_json():
    try:
        from modules.v50_world_class_institutional_stack import v46_dark_pool
        return jsonify(v46_dark_pool())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v50_bp.route("/v47/macro", methods=["GET"])
def v47_macro_json():
    try:
        from modules.v50_world_class_institutional_stack import v47_macro_engine
        return jsonify(v47_macro_engine())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v50_bp.route("/v48/monte-carlo", methods=["GET"])
def v48_monte_carlo_json():
    try:
        from modules.v50_world_class_institutional_stack import v48_monte_carlo
        return jsonify(v48_monte_carlo())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v50_bp.route("/v49/self-learning", methods=["GET"])
def v49_self_learning_json():
    try:
        from modules.v50_world_class_institutional_stack import v49_self_learning
        return jsonify(v49_self_learning())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@v50_bp.route("/v50/optimizer", methods=["GET"])
def v50_optimizer_json():
    try:
        from modules.v50_world_class_institutional_stack import v50_portfolio_optimizer
        return jsonify(v50_portfolio_optimizer())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200
