import os
import sys
import time
import signal
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --------------------------------------------------
# Logging configuration
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --------------------------------------------------
# Global state
# --------------------------------------------------
app_user_id = None
app_user_secret = None

HEALTH_PORT = int(os.getenv("HEALTH_PORT", "18080"))
shutdown_requested = False

# --------------------------------------------------
# Secret handling
# --------------------------------------------------
def load_secrets():
    global app_user_id, app_user_secret

    app_user_id = os.getenv("APP_USER_ID")
    app_user_secret = os.getenv("APP_USER_SECRET")

    if not app_user_id or not app_user_secret:
        logging.error("Missing application credentials")
        return False

    # Enforce minimal secret quality (no hard‑coded value)
    if len(app_user_secret) < 12:
        logging.error("Application secret too short")
        return False

    logging.info("Secrets loaded successfully")
    return True


def handle_reload(signum, frame):
    logging.info("Reload signal received, reloading secrets")
    load_secrets()


def handle_shutdown(signum, frame):
    global shutdown_requested
    logging.info("Shutdown signal received, exiting cleanly")
    shutdown_requested = True


# --------------------------------------------------
# HTTP Health Endpoint
# --------------------------------------------------
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

    # Disable default noisy logging
    def log_message(self, format, *args):
        return


def start_http_server():
    server = HTTPServer(("127.0.0.1", HEALTH_PORT), HealthHandler)
    logging.info(
        f"Health endpoint listening on http://127.0.0.1:{HEALTH_PORT}/health"
    )
    server.serve_forever()


# --------------------------------------------------
# Main application
# --------------------------------------------------
def main():
    logging.info("Secure App starting")

    if not load_secrets():
        sys.exit(1)

    # Signal handling
    signal.signal(signal.SIGHUP, handle_reload)
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Start health endpoint in background thread
    threading.Thread(
        target=start_http_server,
        daemon=True
    ).start()

    logging.info("Application running (supports reload & graceful shutdown)")

    # Main loop
    while not shutdown_requested:
        logging.info("Heartbeat: app is alive")
        time.sleep(10)

    logging.info("Application stopped cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()
