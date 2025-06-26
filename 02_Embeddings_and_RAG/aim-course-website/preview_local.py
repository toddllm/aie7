#!/usr/bin/env python3
"""
Local preview server for the AIM Course website
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 8000
DIRECTORY = "."

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Route requests properly
        if self.path == '/':
            self.path = '/frontend/index.html'
        elif self.path.startswith('/static/'):
            # Static files are already in the right place
            pass
        elif not self.path.startswith('/frontend/'):
            # Assume other paths should go to frontend
            self.path = f'/frontend{self.path}'
        
        return super().do_GET()

def main():
    print(f"🌐 Starting local preview server on http://localhost:{PORT}")
    print("📁 Serving files from current directory")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Create a simple index redirect
    if not os.path.exists("index.html"):
        with open("index.html", "w") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=frontend/index.html">
</head>
<body>
    <p>Redirecting to <a href="frontend/index.html">AIM Course Website</a>...</p>
</body>
</html>
""")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        # Open browser
        webbrowser.open(f'http://localhost:{PORT}')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✋ Server stopped")
            # Clean up temporary index
            if os.path.exists("index.html"):
                os.remove("index.html")

if __name__ == "__main__":
    main()