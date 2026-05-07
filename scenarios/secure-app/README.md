# Secure Linux Service Baseline

In this scenario, you will build and run a production-grade Linux service
step by step. Nothing is pre-installed for you — you will create everything
explicitly, just like on a real server.

---

## Step 1: Create the application

Run the following command to create the application file.

```bash
cat <<'EOF' > app.py
import os
import sys
import time
import signal
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app_user_id = None
app_user_secret = None
shutdown_requested = False
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "18080"))

def load_secrets():
    global app_user_id, app_user_secret

    app_user_id = os.getenv("APP_USER_ID")
    app_user_secret = os.getenv("APP_USER_SECRET")

    if not app_user_id or not app_user_secret:
        logging.error("Missing application credentials")
        return False

    if len(app_user_secret) < 12:
        logging.error("Application secret too short")
        return False

    logging.info("Secrets loaded successfully")
    return True

def handle_reload(signum, frame):
    logging.info("Reload signal received")
    load_secrets()

def handle_shutdown(signum, frame):
    global shutdown_requested
    logging.info("Shutdown signal received")
    shutdown_requested = True

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def start_http_server():
    server = HTTPServer(("127.0.0.1", HEALTH_PORT), HealthHandler)
    logging.info(f"Health endpoint on port {HEALTH_PORT}")
    server.serve_forever()

def main():
    logging.info("Secure App starting")

    if not load_secrets():
        sys.exit(1)

    signal.signal(signal.SIGHUP, handle_reload)
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    threading.Thread(target=start_http_server, daemon=True).start()

    while not shutdown_requested:
        logging.info("App is running")
        time.sleep(10)

    logging.info("App stopped cleanly")

if __name__ == "__main__":
    main()
EOF
