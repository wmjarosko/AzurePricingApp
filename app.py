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
    operating_system = data.get('operating_system')
    server_configs = data.get('server_configs')

    if not all([environment_name, subscriber_count, price_tolerance, region, operating_system, server_configs]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Extract counts from the server_configs object for the pricing script
    server_counts = {name: config['count'] for name, config in server_configs.items()}

    # Call your main pricing function with the data from the front-end
    # Note: pricing_script is not yet updated to handle server_configs, this will be done in Phase 2
    recommendations, total_cost = get_total_estimated_monthly_cost(
        environment_name=environment_name,
        subscriber_count=int(subscriber_count),
        price_tolerance=price_tolerance,
        region=region,
        operating_system=operating_system,
        server_counts=server_counts
    )

    # For now, just echo back the categories in the recommendations
    for server_name, config in server_configs.items():
        if server_name in recommendations:
            recommendations[server_name]['category'] = config.get('category', 'N/A')

    response = {
        "environment_name": environment_name,
        "operating_system": operating_system,
        "recommendations": recommendations,
        "total_cost": total_cost
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
