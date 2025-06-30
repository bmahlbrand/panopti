# panopti/server/__init__.py
from .app import create_app, run_standalone_server

__all__ = ['create_app', 'run_standalone_server']

def start_server(host='localhost', port=8080, debug=False):
    """
    Start a standalone panopti server that doesn't block, can be imported
    and run directly to start a server without creating a viewer
    """
    run_standalone_server(host=host, port=port, debug=debug)