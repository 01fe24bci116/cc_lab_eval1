import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory dictionary of menu items
MENU = {
    "1": {
        "item_id": "1",
        "name": "Margherita Pizza",
        "category": "Pizza",
        "price": 12.99,
        "available": True,
        "description": "Classic cheese and tomato pizza with fresh basil"
    },
    "2": {
        "item_id": "2",
        "name": "Veg Burger",
        "category": "Burgers",
        "price": 8.49,
        "available": True,
        "description": "Crispy vegetable patty with lettuce, tomato, and vegan mayo"
    },
    "3": {
        "item_id": "3",
        "name": "Pasta Alfredo",
        "category": "Pasta",
        "price": 10.99,
        "available": True,
        "description": "Fettuccine pasta in rich creamy parmesan garlic sauce"
    },
    "4": {
        "item_id": "4",
        "name": "Garlic Bread",
        "category": "Sides",
        "price": 4.99,
        "available": False,
        "description": "Toasted baguette with garlic butter and herbs (Currently Sold Out)"
    },
    "pizza": {
        "item_id": "pizza",
        "name": "Margherita Pizza",
        "category": "Pizza",
        "price": 12.99,
        "available": True,
        "description": "Classic cheese and tomato pizza with fresh basil"
    },
    "burger": {
        "item_id": "burger",
        "name": "Veg Burger",
        "category": "Burgers",
        "price": 8.49,
        "available": True,
        "description": "Crispy vegetable patty with lettuce, tomato, and vegan mayo"
    },
    "pasta": {
        "item_id": "pasta",
        "name": "Pasta Alfredo",
        "category": "Pasta",
        "price": 10.99,
        "available": True,
        "description": "Fettuccine pasta in rich creamy parmesan garlic sauce"
    }
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "restaurant-service",
        "total_items": len(MENU)
    }), 200


@app.route("/menu", methods=["GET"])
@app.route("/menu/", methods=["GET"])
def get_menu():
    item_id = request.args.get("item_id")
    if item_id:
        return fetch_item(item_id)
    return jsonify({
        "service": "restaurant-service",
        "count": len(MENU),
        "items": MENU
    }), 200


@app.route("/menu/<item_id>", methods=["GET"])
def get_menu_item(item_id):
    return fetch_item(item_id)


def fetch_item(item_id):
    key = str(item_id).strip().lower()
    item = MENU.get(key)
    if not item:
        return jsonify({
            "error": "Item not found",
            "message": f"Menu item '{item_id}' does not exist in the restaurant catalog."
        }), 404

    if not item.get("available", False):
        return jsonify({
            "error": "Item unavailable",
            "message": f"Menu item '{item.get('name')}' is currently out of stock.",
            "item": item
        }), 400

    return jsonify(item), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, threaded=True)
