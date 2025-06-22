#!/usr/bin/env python3

import os
from flask import Flask, request
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Restaurant, Pizza, RestaurantPizza

# ---------- Configuration ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# ---------- Root Route ----------
@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# ---------- Resources ----------

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [r.to_dict(rules=("-restaurant_pizzas",)) for r in restaurants], 200

class RestaurantByID(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)
        if not restaurant:
            return {"error": "Restaurant not found"}, 404
        return restaurant.to_dict(rules=(
            "-restaurant_pizzas.restaurant",
            "-restaurant_pizzas.pizza.restaurant_pizzas",
        )), 200

    def delete(self, id):
        restaurant = db.session.get(Restaurant, id)
        if not restaurant:
            return {"error": "Restaurant not found"}, 404
        db.session.delete(restaurant)
        db.session.commit()
        return "", 204

class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [p.to_dict(rules=("-restaurant_pizzas",)) for p in pizzas], 200

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        try:
            restaurant_pizza = RestaurantPizza(
                price=data["price"],
                pizza_id=data["pizza_id"],
                restaurant_id=data["restaurant_id"]
            )
            db.session.add(restaurant_pizza)
            db.session.commit()

            return restaurant_pizza.to_dict(rules=(
                "-restaurant.restaurant_pizzas",
                "-pizza.restaurant_pizzas"
            )), 201

        except Exception:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400

# ---------- Route Registration ----------
api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantByID, "/restaurants/<int:id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas")

# ---------- Entry Point ----------
if __name__ == "__main__":
    app.run(port=5555, debug=True)
