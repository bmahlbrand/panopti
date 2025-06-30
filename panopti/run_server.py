# panopti/run_server.py
import argparse
from .viewer import start_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start a panopti server')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    print(args)
    print(f"Starting panopti server at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    # Start the server
    start_server(host=args.host, port=args.port, debug=args.debug)