
import http.server
import socketserver
import webbrowser
import os
import sys
import subprocess
import json
import time

PORT = 8001

class TradingRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/run_trading':
            print("Received request to run trading session...")
            
            # Send initial headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            try:
                # Run main.py and capture output
                # We use sys.executable to ensure we use the same python env
                process = subprocess.run(
                    [sys.executable, 'main.py'],
                    cwd=os.getcwd(),
                    capture_output=True,
                    text=True,
                    encoding='utf-8' # Force utf-8 reading
                )
                
                output = process.stdout
                error = process.stderr
                
                if process.returncode != 0:
                    print(f"Error running script: {error}")
                else:
                    print("Script executed successfully.")

                response_data = {
                    'success': process.returncode == 0,
                    'output': output,
                    'error': error
                }
                
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            except Exception as e:
                print(f"Exception during execution: {e}")
                error_response = {
                    'success': False,
                    'output': '',
                    'error': str(e)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

    def end_headers(self):
        # Add CORS headers to allow loading local files (GET requests)
        self.send_header('Access-Control-Allow-Origin', '*')
        
        # Disable caching for data files to ensure dashboard sees live updates
        if self.path.endswith('.json') or self.path.endswith('.csv'):
             self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
             self.send_header("Pragma", "no-cache")
             self.send_header("Expires", "0")
        super().end_headers()

def run_server():
    # Only try to open browser if not already running (simple check)
    url = f"http://localhost:{PORT}/dashboard.html"
    
    print(f"Starting Trading Server at {url}")
    print("API Endpoint active: POST /api/run_trading")

    # Allow reusing address to fix 'Address already in use' errors during restarts
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), TradingRequestHandler) as httpd:
            print("Server running... (Press Ctrl+C to stop)")
            # Open browser automatically
            webbrowser.open(url)
            httpd.serve_forever()
    except OSError as e:
        print(f"Error: Port {PORT} is likely in use.")
        print("Please stop the other Python process or close the terminal window running it.")
        print("Then restart this script.")

if __name__ == "__main__":
    run_server()
