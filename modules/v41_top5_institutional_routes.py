from flask import Blueprint, jsonify
from modules.v41_top5_institutional_core import build_top5, V41_VERSION

v41_top5_bp = Blueprint("v41_top5", __name__)

@v41_top5_bp.route("/v41/top5-module", methods=["GET"])
def top5_module():
    return jsonify({"ok": True, "version": V41_VERSION, "top5": build_top5()})
