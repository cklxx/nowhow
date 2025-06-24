import uvicorn
from api.main import app

def main():
    """Start the API server"""
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
