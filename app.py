from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import dotenv_values
from functools import wraps

app = Flask(__name__)
CORS(app)
SECRETS = dotenv_values(".env")


def api_key_required(f):
    """
    Validates the API KEY sent on the request
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = SECRETS.get("API_KEY", 'True')
        headers = request.headers
        try:
            if headers.get('x-api-key', None) == api_key:
                pass
            else:
                return jsonify({"message": "invalid api key"}), 401
        except:
            return jsonify({"message": "invalid api key"}), 401
        return f(*args, **kwargs)
    return decorated


@app.errorhandler(404)
def resource_not_found(e):
    """Page not found
    Args:
        e (Error): Page not found error raised by Flask
    Returns:
        JSON: The same error raised
    """
    return jsonify(error=str(e)), 404


@app.route('/', methods=['GET'])
def test():
    """
    Sanity test to confirm backend is working
    """
    return "Working!", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(SECRETS.get("PORT")))
