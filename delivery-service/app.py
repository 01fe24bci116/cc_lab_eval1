import os
import random
import uuid
from flask import Flask, jsonify, request

app = Flask(__name__)

# Delivery driver pool
DRIVER_POOL = [
    {"driver_id": "DRV-101", "name": "Alice Smith", "vehicle": "Electric Scooter", "rating": 4.9},
    {"driver_id": "DRV-102", "name": "Bob Jones", "vehicle": "Motorcycle", "rating": 4.8},
    {"driver_id": "DRV-103", "name": "Charlie Brown", "vehicle": "Bicycle", "rating": 4.7},
    {"driver_id": "DRV-104", "name": "David Miller", "vehicle": "Car", "rating": 4.9},
    {"driver_id": "DRV-105", "name": "Emma Wilson", "vehicle": "Electric Scooter", "rating": 5.0}
]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "delivery-service",
        "available_drivers": len(DRIVER_POOL)
    }), 200


@app.route("/drivers", methods=["GET"])
def list_drivers():
    return jsonify({
        "service": "delivery-service",
        "drivers": DRIVER_POOL
    }), 200


@app.route("/assign-delivery", methods=["POST"])
def assign_delivery():
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id", f"ORD-{uuid.uuid4().hex[:8].upper()}")
    customer_name = data.get("customer_name", "Valued Customer")

    # Randomly select a driver from the pool
    driver = random.choice(DRIVER_POOL)

    # Calculate estimated delivery time in minutes (15 to 35 mins)
    eta_minutes = random.randint(15, 35)
    delivery_id = f"DEL-{uuid.uuid4().hex[:8].upper()}"

    assignment = {
        "delivery_id": delivery_id,
        "order_id": order_id,
        "driver_id": driver["driver_id"],
        "driver_name": driver["name"],
        "vehicle": driver["vehicle"],
        "driver_rating": driver["rating"],
        "eta_minutes": eta_minutes,
        "status": "ASSIGNED",
        "assigned_to": customer_name
    }

    return jsonify(assignment), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, threaded=True)
