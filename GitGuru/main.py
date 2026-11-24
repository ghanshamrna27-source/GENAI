from app.cli import start
from app.main import app  # Expose FastAPI ASGI app for uvicorn main:app

if __name__ == "__main__":
    start()
