import os
import sys

# Add the project root directory to Python's sys.path and set working directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Adapt FastAPI (ASGI) to Passenger (WSGI)
from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
