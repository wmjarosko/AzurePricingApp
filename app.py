# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from pricing_script import get_total_estimated_monthly_cost

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from pricing_script import get_total_estimated_monthly_cost

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# New route for the root URL
@app.route('/', methods=['GET'])
def index():
    return "<h1>Hello from Flask! Your server is running.</h1>"

# This is the API endpoint that the front-end will call
@app.route('/calculate', methods=['POST'])
def calculate_cost():
    data = request.get_json()

    environment_name = data.get('environment_name')
    subscriber_count = data.get('subscriber_count')
    price_tolerance = data.get('price_tolerance')
    region = data.get('region')
    server_counts = data.get('server_counts')

    if not all([environment_name, subscriber_count, price_tolerance, region, server_counts]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Call your main pricing function with the data from the front-end
    recommendations, total_cost = get_total_estimated_monthly_cost(
        environment_name=environment_name,
        subscriber_count=int(subscriber_count),
        price_tolerance=price_tolerance,
        region=region,
        server_counts=server_counts
    )

    response = {
        "environment_name": environment_name,
        "recommendations": recommendations,
        "total_cost": total_cost
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
