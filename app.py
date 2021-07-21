import parse as parse_server
import one_signal
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


@app.route('/push', methods=['GET'])
def notify():
    """
    Send a push notification to all users suscribed to the user sent with the place that was just posted by it
    """
    try:
        userId = request.args["user"]
        placeId = request.args["place"]
    except KeyError:
        return "Place and user need to be on request", 400
    
    # Get user and place from Parse
    user = parse_server.get_user(objectId=userId)
    place = parse_server.get_place(objectId=placeId)
    
    # Get subscribers to that user
    subs = parse_server.get_subscriptions(user=user)
    
    # Create toUsers list
    toUsers = []
    for sub in subs:
        if sub.toUser.OneSignal is not None and len(sub.toUser.OneSignal) > 0:
            toUsers.append(sub.toUser.OneSignal)
    
    one_signal.push(place=place.objectId, toUsers=toUsers, title=f"{str(user.name).capitalize()} has posted a new place", text="Click and see this amazing place!")
    
    print(f"Sent {len(toUsers)} notifications!")
    
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(SECRETS.get("PORT")))