import os
import uuid
import datetime
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Service endpoints configured via environment variables
RESTAURANT_SERVICE_URL = os.environ.get("RESTAURANT_SERVICE_URL", "http://restaurant-service:5001")
DELIVERY_SERVICE_URL = os.environ.get("DELIVERY_SERVICE_URL", "http://delivery-service:5002")

# In-memory store for orders
ORDERS = []


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "order-service",
        "restaurant_service_url": RESTAURANT_SERVICE_URL,
        "delivery_service_url": DELIVERY_SERVICE_URL,
        "total_orders_placed": len(ORDERS)
    }), 200


@app.route("/orders", methods=["GET"])
def get_orders():
    return jsonify({
        "service": "order-service",
        "total_orders": len(ORDERS),
        "orders": ORDERS
    }), 200


@app.route("/order", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error": "Invalid request payload",
            "message": "JSON body must be provided"
        }), 400

    customer_name = data.get("customer_name")
    item_id = data.get("item_id")

    if not customer_name or not item_id:
        return jsonify({
            "error": "Missing required fields",
            "message": "Both 'customer_name' and 'item_id' are required"
        }), 400

    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    # Step 1: Synchronously check item availability from restaurant-service
    restaurant_url = f"{RESTAURANT_SERVICE_URL}/menu/{item_id}"
    try:
        menu_resp = requests.get(restaurant_url, timeout=5)
        if menu_resp.status_code == 404:
            # Fallback to query parameter check on /menu/
            menu_resp = requests.get(f"{RESTAURANT_SERVICE_URL}/menu/", params={"item_id": item_id}, timeout=5)
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Restaurant service unreachable",
            "message": "Failed to connect to restaurant-service",
            "details": str(e)
        }), 503

    if menu_resp.status_code == 404:
        return jsonify({
            "error": "Item not found",
            "message": f"Menu item '{item_id}' not found in restaurant-service"
        }), 404

    if menu_resp.status_code == 400:
        return jsonify({
            "error": "Item unavailable",
            "message": f"Menu item '{item_id}' is currently unavailable for order"
        }), 400

    if menu_resp.status_code != 200:
        return jsonify({
            "error": "Restaurant service error",
            "status_code": menu_resp.status_code,
            "details": menu_resp.text
        }), menu_resp.status_code

    item_data = menu_resp.json()

    # Step 2: Synchronously assign delivery driver via delivery-service
    delivery_url = f"{DELIVERY_SERVICE_URL}/assign-delivery"
    delivery_payload = {
        "order_id": order_id,
        "customer_name": customer_name,
        "item_id": item_id
    }
    try:
        delivery_resp = requests.post(delivery_url, json=delivery_payload, timeout=5)
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Delivery service unreachable",
            "message": "Failed to connect to delivery-service",
            "details": str(e)
        }), 503

    if delivery_resp.status_code not in (200, 201):
        return jsonify({
            "error": "Delivery assignment failed",
            "status_code": delivery_resp.status_code,
            "details": delivery_resp.text
        }), 502

    delivery_data = delivery_resp.json()

    # Step 3: Aggregate confirmation response
    order_confirmation = {
        "order_id": order_id,
        "customer_name": customer_name,
        "status": "CONFIRMED",
        "item": item_data,
        "delivery": delivery_data,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    ORDERS.append(order_confirmation)
    return jsonify(order_confirmation), 201


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
