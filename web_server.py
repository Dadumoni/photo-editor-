import os
import threading
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import photo_editor_bot

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        # Suppress log messages to reduce console noise
        return

def run_server():
    port = int(os.environ.get('PORT', 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f'Starting health check server on port {port}...')
    httpd.serve_forever()

def keep_alive():
    """Send requests to the server periodically to keep it awake"""
    app_name = os.environ.get('KOYEB_APP_NAME', 'photo-editor-bot')
    
    # Wait for server to start
    time.sleep(60)
    
    while True:
        try:
            # Get the public URL from environment or use localhost for testing
            url = os.environ.get('PUBLIC_URL', f'http://localhost:8000')
            response = requests.get(url)
            print(f"Keep-alive ping sent. Status: {response.status_code}")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
        
        # Wait for 5 minutes before next ping
        time.sleep(300)

if __name__ == '__main__':
    # Start the health check server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Start the keep-alive ping in another thread
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    # Start the Telegram bot
    photo_editor_bot.main() 