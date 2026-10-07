# Food Ordering System - Python + MongoDB

A beginner-friendly college project using Flask, Python and MongoDB.

## Features
- User registration and login
- Food menu
- Add to cart
- Increase/decrease/remove cart items
- Checkout
- Order history
- Admin dashboard
- Add/delete food
- Update order status
- MongoDB database

## Requirements
- Python 3.10+
- MongoDB Community Server OR MongoDB Atlas
- VS Code

## Setup

1. Open this project in VS Code.
2. Create a virtual environment:

   python -m venv venv

3. Activate it on Windows:

   venv\Scripts\activate

4. Install packages:

   pip install -r requirements.txt

5. Make sure MongoDB is running locally.

   Default connection:
   mongodb://localhost:27017/

   Or set MONGO_URI to your MongoDB Atlas connection string.

6. Run:

   python app.py

7. Open:
   http://127.0.0.1:5000/

## MongoDB
Database name: food_ordering

Collections:
- users
- foods
- orders

## Admin
For this academic demo, the admin page is:
http://127.0.0.1:5000/admin

For a production application, add proper admin authentication before using admin functions.
