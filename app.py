from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "food-ordering-demo-secret")

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["food_ordering"]

users = db["users"]
foods = db["foods"]
orders = db["orders"]

# Seed sample food data
if foods.count_documents({}) == 0:
    foods.insert_many([
        {"name": "Margherita Pizza", "category": "Pizza", "price": 199, "description": "Classic cheese and tomato pizza", "available": True},
        {"name": "Paneer Pizza", "category": "Pizza", "price": 249, "description": "Paneer with capsicum and onion", "available": True},
        {"name": "Veg Burger", "category": "Burger", "price": 129, "description": "Crispy veg patty with fresh vegetables", "available": True},
        {"name": "French Fries", "category": "Snacks", "price": 99, "description": "Crispy golden french fries", "available": True},
        {"name": "White Sauce Pasta", "category": "Pasta", "price": 179, "description": "Creamy white sauce pasta", "available": True},
        {"name": "Cold Coffee", "category": "Drinks", "price": 109, "description": "Chilled creamy cold coffee", "available": True}
    ])

@app.route("/")
def index():
    food_list = list(foods.find({"available": True}))
    return render_template("index.html", foods=food_list)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if users.find_one({"email": email}):
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        users.insert_one({
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "created_at": datetime.now()
        })
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            return redirect(url_for("index"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/add-to-cart/<food_id>")
def add_to_cart(food_id):
    food = foods.find_one({"_id": ObjectId(food_id), "available": True})
    if not food:
        flash("Food item not found.", "danger")
        return redirect(url_for("index"))

    cart = session.get("cart", {})
    key = str(food["_id"])
    cart[key] = cart.get(key, 0) + 1
    session["cart"] = cart
    flash(f"{food['name']} added to cart.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/cart")
def cart():
    cart_data = []
    total = 0
    for food_id, quantity in session.get("cart", {}).items():
        food = foods.find_one({"_id": ObjectId(food_id)})
        if food:
            subtotal = food["price"] * quantity
            total += subtotal
            cart_data.append({"food": food, "quantity": quantity, "subtotal": subtotal})
    return render_template("cart.html", cart=cart_data, total=total)

@app.route("/update-cart/<food_id>/<action>")
def update_cart(food_id, action):
    cart = session.get("cart", {})
    if food_id in cart:
        if action == "increase":
            cart[food_id] += 1
        elif action == "decrease":
            cart[food_id] -= 1
            if cart[food_id] <= 0:
                del cart[food_id]
        elif action == "remove":
            del cart[food_id]
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        flash("Please login before checkout.", "warning")
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))

    items = []
    total = 0
    for food_id, quantity in cart.items():
        food = foods.find_one({"_id": ObjectId(food_id), "available": True})
        if food:
            subtotal = food["price"] * quantity
            total += subtotal
            items.append({
                "food_id": str(food["_id"]),
                "name": food["name"],
                "price": food["price"],
                "quantity": quantity,
                "subtotal": subtotal
            })

    if request.method == "POST":
        order = {
            "user_id": session["user_id"],
            "customer_name": session["user_name"],
            "address": request.form["address"],
            "phone": request.form["phone"],
            "items": items,
            "total": total,
            "status": "Pending",
            "created_at": datetime.now()
        }
        orders.insert_one(order)
        session["cart"] = {}
        flash("Order placed successfully!", "success")
        return redirect(url_for("my_orders"))

    return render_template("checkout.html", items=items, total=total)

@app.route("/orders")
def my_orders():
    if "user_id" not in session:
        return redirect(url_for("login"))
    order_list = list(orders.find({"user_id": session["user_id"]}).sort("created_at", -1))
    return render_template("orders.html", orders=order_list)

# Simple admin dashboard: use /admin
@app.route("/admin")
def admin():
    food_list = list(foods.find())
    order_list = list(orders.find().sort("created_at", -1))
    return render_template("admin.html", foods=food_list, orders=order_list)

@app.route("/admin/add-food", methods=["POST"])
def add_food():
    foods.insert_one({
        "name": request.form["name"],
        "category": request.form["category"],
        "price": float(request.form["price"]),
        "description": request.form["description"],
        "available": True
    })
    flash("Food added.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/delete-food/<food_id>")
def delete_food(food_id):
    foods.delete_one({"_id": ObjectId(food_id)})
    flash("Food deleted.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/status/<order_id>/<status>")
def update_order_status(order_id, status):
    allowed = ["Pending", "Preparing", "Out for Delivery", "Delivered", "Cancelled"]
    if status in allowed:
        orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": status}})
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
