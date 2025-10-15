import sys
import os
from app import app, create_tables

def main():
    try:
        print("Creating database tables...")
        create_tables()
        
        print("Starting Flask application...")
        port = 5000
        host = '127.0.0.1'
        
        print(f"Server will be available at http://{host}:{port}")
        app.run(debug=True, host=host, port=port)
        
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()