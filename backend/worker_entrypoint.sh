#!/bin/bash
# Start a minimal HTTP server for Cloud Run health checks on port 8080
python -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self, *a): pass
HTTPServer(('0.0.0.0', 8080), H).serve_forever()
" &

# Start Celery worker with beat scheduler
exec celery -A config worker --beat -l info
