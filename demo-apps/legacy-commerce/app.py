"""Source for static inspection only. ModernizeIQ must never import this file."""
from flask import Flask
import config

app = Flask(__name__)


@app.route("/orders")
def orders():
    return {"orders": [], "fixture": True}


def total(items):
    return sum(item["price"] * item["quantity"] for item in items)
