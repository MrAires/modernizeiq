"""Static control fixture. Runtime correctness is not asserted by its presence."""
import logging
from flask import Flask

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.get("/health")
def health():
    return {"status": "ok"}
