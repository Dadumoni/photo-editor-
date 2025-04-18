import os
import threading
import time
import logging
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import photo_editor_bot
import random

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("keep_alive")

# Global flag for keep-alive tracking
is_active = True

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
    """Run the HTTP server for health checks"""
    port = int(os.environ.get('PORT', 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f'Starting health check server on port {port}...')
    httpd.serve_forever()

def keep_alive_aggressive():
    """Send frequent requests to keep the server awake (every 2-4 seconds)"""
    # Wait for server to start
    time.sleep(10)
    
    logger.info("Starting AGGRESSIVE keep-alive mechanism - pinging every 2-4 seconds")
    
    ping_count = 0
    while is_active:
        try:
            # Get the public URL from environment or use localhost for testing
            url = os.environ.get('PUBLIC_URL', f'http://localhost:8000')
            response = requests.get(url, timeout=5)
            
            ping_count += 1
            # Only log every 100 pings to reduce log noise
            if ping_count % 100 == 0:
                logger.info(f"Keep-alive ping #{ping_count} sent. Status: {response.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        
        # Randomize the interval slightly to avoid predictable patterns
        # Sleep between 2-4 seconds
        time.sleep(random.uniform(2, 4))

def keep_alive_external():
    """Use an external service (UptimeRobot-like approach) to ping our server"""
    # Wait a bit longer for this strategy
    time.sleep(30)
    
    logger.info("Starting EXTERNAL keep-alive mechanism")
    
    # Define multiple external ping services
    ping_services = [
        "https://api.koyeb.com/v1/ping", # Koyeb's own API
        "https://www.google.com",        # Just to get network activity
    ]
    
    ping_count = 0
    while is_active:
        try:
            # Ping our own service
            own_url = os.environ.get('PUBLIC_URL', f'http://localhost:8000')
            requests.get(own_url, timeout=5)
            
            # Also ping an external service to generate outbound traffic
            for service in ping_services:
                try:
                    requests.get(service, timeout=5)
                except:
                    pass  # Ignore errors from external services
            
            ping_count += 1
            if ping_count % 20 == 0:
                logger.info(f"External ping #{ping_count} completed")
                
        except Exception as e:
            logger.warning(f"External ping failed: {e}")
        
        # Sleep for 15 seconds between external pings
        time.sleep(15)

def cpu_activity():
    """Generate minimal CPU activity to prevent idling"""
    time.sleep(45)  # Wait for other things to start
    
    logger.info("Starting minimal CPU activity to prevent idling")
    
    activity_count = 0
    while is_active:
        try:
            # Do a small computation to generate CPU activity
            # This is intentionally lightweight but enough to register activity
            for _ in range(10000):
                _ = random.random() * random.random()
            
            activity_count += 1
            if activity_count % 30 == 0:
                logger.info(f"Generated CPU activity #{activity_count}")
        except Exception as e:
            logger.warning(f"CPU activity generation failed: {e}")
        
        # Sleep for 10 seconds between CPU activities
        time.sleep(10)

def memory_activity():
    """Periodically allocate and free memory to show activity"""
    time.sleep(60)  # Wait even longer for this strategy
    
    logger.info("Starting periodic memory allocation to show activity")
    
    activity_count = 0
    while is_active:
        try:
            # Allocate a small array temporarily
            temp_array = bytearray(1024 * 1024)  # 1MB
            # Do something with it to prevent optimization
            for i in range(0, len(temp_array), 1024):
                temp_array[i] = random.randint(0, 255)
            
            # Let it be garbage collected
            del temp_array
            
            activity_count += 1
            if activity_count % 10 == 0:
                logger.info(f"Memory activity #{activity_count} completed")
        except Exception as e:
            logger.warning(f"Memory activity failed: {e}")
        
        # Sleep for 30 seconds between memory activities
        time.sleep(30)

def keep_alive_master():
    """Master thread that manages all keep-alive strategies"""
    keep_alive_mode = os.environ.get('KEEP_ALIVE_MODE', 'aggressive').lower()
    logger.info(f"Initializing keep-alive system in {keep_alive_mode} mode")
    
    # Start the appropriate strategy based on configuration
    if keep_alive_mode == 'aggressive':
        # Start all strategies for maximum effect
        threads = [
            threading.Thread(target=keep_alive_aggressive),
            threading.Thread(target=keep_alive_external),
            threading.Thread(target=cpu_activity),
            threading.Thread(target=memory_activity)
        ]
    else:
        # Use a more conservative approach
        threads = [
            threading.Thread(target=keep_alive_aggressive),
            threading.Thread(target=keep_alive_external)
        ]
    
    # Start all threads as daemon threads
    for thread in threads:
        thread.daemon = True
        thread.start()
    
    logger.info(f"Started {len(threads)} keep-alive strategies")

if __name__ == '__main__':
    try:
        # Start the health check server in a separate thread
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Start the keep-alive master in another thread
        keep_alive_thread = threading.Thread(target=keep_alive_master)
        keep_alive_thread.daemon = True
        keep_alive_thread.start()
        
        # Start the Telegram bot
        logger.info("Starting main Telegram bot...")
        photo_editor_bot.main()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        is_active = False
    except Exception as e:
        logger.error(f"Error in main thread: {e}")
        is_active = False 