from flask import jsonify


def api_response(success=True, data=None, error=None, status=200):
    return jsonify({"success": success, "data": data, "error": error}), status
