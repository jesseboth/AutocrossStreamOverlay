#!/usr/bin/env python3
import http.server
import ssl
import socketserver
import os
import sys
import mimetypes
import threading
import json
from pathlib import Path
from io import BytesIO

# Configuration
HTTPS_PORT = 1900
HTTP_PORT = 1901
HOST = '0.0.0.0'
CERT_FILE = 'server/server.crt'
KEY_FILE = 'server/server.key'

# Files to hide from web access
HIDDEN_FILES = {
    'server.key', 'server.crt', 'https_server.py', 
    '.gitignore', '.env', 'config.ini'
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.gif', '.svg'}

# Simple P2P signaling storage
p2p_signaling = {
    'offer': None,
    'answer': None
}

# GPS data storage
gps_data_storage = {
    'data': None,
    'timestamp': 0
}

class SecureHTTPSHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Remove query parameters and normalize path
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        
        # Decode percent-encoded characters
        import urllib.parse
        path = urllib.parse.unquote(path)
        
        # Handle CA certificate download
        if path == '/ca.crt':
            return os.path.join(os.getcwd(), 'server/ca.crt')
        
        # Remove leading slash and map to public directory
        if path.startswith('/'):
            path = path[1:]
        
        # If path is empty, default to public directory
        if not path:
            path = 'public'
        else:
            # Prepend 'public/' to all paths
            path = 'public/' + path
        
        # Convert to absolute path
        translated_path = os.path.join(os.getcwd(), path)
        
        # Normalize the path to prevent directory traversal
        translated_path = os.path.normpath(translated_path)
        
        # Ensure the path is within the public directory
        public_dir = os.path.join(os.getcwd(), 'public')
        if not translated_path.startswith(public_dir):
            return None
        
        filename = os.path.basename(translated_path)
        
        # Block hidden files
        if filename in HIDDEN_FILES:
            return None
            
        # Check file extension for files (not directories)
        if os.path.isfile(translated_path):
            _, ext = os.path.splitext(filename)
            if ext.lower() not in ALLOWED_EXTENSIONS:
                return None
                
        return translated_path
    
    def do_GET(self):
        # Handle P2P signaling API endpoints
        if self.path == '/api/offer':
            self.handle_get_offer()
            return
        elif self.path == '/api/answer':
            self.handle_get_answer()
            return
        elif self.path == '/api/gps-data':
            self.handle_get_gps_data()
            return
        
        # Check if path should be blocked
        translated_path = self.translate_path(self.path)
        if translated_path is None:
            self.send_error(404, "File not found")
            return
        
        # Handle CA certificate download with proper MIME type
        if translated_path.endswith('server/ca.crt'):
            self.serve_ca_certificate(translated_path)
            return
            
        # Continue with normal GET handling
        super().do_GET()
    
    def do_POST(self):
        # Handle P2P signaling API endpoints
        if self.path == '/api/offer':
            self.handle_post_offer()
            return
        elif self.path == '/api/answer':
            self.handle_post_answer()
            return
        elif self.path == '/api/gps-data':
            self.handle_post_gps_data()
            return
        
        # Default POST handling
        self.send_error(405, "Method not allowed")
    
    def handle_get_offer(self):
        """Get the current WebRTC offer"""
        global p2p_signaling
        
        response_data = {
            'offer': p2p_signaling['offer']
        }
        
        self.send_json_response(response_data)
    
    def handle_post_offer(self):
        """Store a WebRTC offer"""
        global p2p_signaling
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            p2p_signaling['offer'] = data.get('offer')
            p2p_signaling['answer'] = None  # Reset answer when new offer arrives
            
            self.send_json_response({'status': 'offer stored'})
            
        except Exception as e:
            self.send_error(400, f"Error processing offer: {e}")
    
    def handle_get_answer(self):
        """Get the current WebRTC answer"""
        global p2p_signaling
        
        response_data = {
            'answer': p2p_signaling['answer']
        }
        
        self.send_json_response(response_data)
    
    def handle_post_answer(self):
        """Store a WebRTC answer"""
        global p2p_signaling
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            p2p_signaling['answer'] = data.get('answer')
            
            self.send_json_response({'status': 'answer stored'})
            
        except Exception as e:
            self.send_error(400, f"Error processing answer: {e}")
    
    def handle_get_gps_data(self):
        """Get the latest GPS data"""
        global gps_data_storage
        import time
        
        # Check if data is recent (within last 5 seconds)
        current_time = time.time()
        if (gps_data_storage['data'] is not None and 
            current_time - gps_data_storage['timestamp'] < 5):
            response_data = {
                'data': gps_data_storage['data'],
                'timestamp': gps_data_storage['timestamp']
            }
        else:
            # No recent data available
            response_data = {
                'data': None,
                'timestamp': 0
            }
        
        self.send_json_response(response_data)
    
    def handle_post_gps_data(self):
        """Store GPS data from sender"""
        global gps_data_storage
        import time
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Store the GPS data with current timestamp
            gps_data_storage['data'] = data
            gps_data_storage['timestamp'] = time.time()
            
            self.send_json_response({'status': 'GPS data stored'})
            
        except Exception as e:
            self.send_error(400, f"Error processing GPS data: {e}")
    
    def send_json_response(self, data):
        """Send a JSON response"""
        response_json = json.dumps(data)
        encoded = response_json.encode('utf-8')
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
    
    def serve_ca_certificate(self, cert_path):
        """Serve the CA certificate with proper MIME type and headers"""
        if not os.path.exists(cert_path):
            self.send_error(404, "CA certificate not found. Run 'python3 ctrl keys' to generate certificates.")
            return
        
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/x-x509-ca-cert")
            self.send_header("Content-Disposition", "attachment; filename=StreamOverlay-CA.crt")
            self.send_header("Content-Length", str(len(cert_data)))
            self.end_headers()
            self.wfile.write(cert_data)
            
        except Exception as e:
            self.send_error(500, f"Error serving certificate: {e}")
    
    def list_directory(self, path):
        """Override to filter directory listings"""
        try:
            file_list = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None
            
        # Filter out hidden files and non-allowed extensions
        filtered_list = []
        for name in file_list:
            if name in HIDDEN_FILES:
                continue
            if os.path.isfile(os.path.join(path, name)):
                _, ext = os.path.splitext(name)
                if ext.lower() not in ALLOWED_EXTENSIONS:
                    continue
            filtered_list.append(name)
        
        # Create HTML listing with filtered files
        try:
            displaypath = self.path
            enc = 'utf-8'
            title = f'Directory listing for {displaypath}'
            
            html_content = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="{enc}">
<title>{title}</title>
</head>
<body>
<h1>{title}</h1>
<hr>
<ul>
'''
            for name in sorted(filtered_list):
                fullname = os.path.join(path, name)
                displayname = linkname = name
                if os.path.isdir(fullname):
                    displayname = name + "/"
                    linkname = name + "/"
                html_content += f'<li><a href="{linkname}">{displayname}</a></li>\n'
            
            html_content += '</ul>\n<hr>\n</body>\n</html>\n'
            
            encoded = html_content.encode(enc, 'surrogateescape')
            f = BytesIO()
            f.write(encoded)
            f.seek(0)
            self.send_response(200)
            self.send_header("Content-type", f"text/html; charset={enc}")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            return f
            
        except Exception:
            self.send_error(500, "Internal server error")
            return None
    
    def end_headers(self):
        # Add security headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging to hide sensitive paths
        message = format % args
        if any(hidden in message for hidden in HIDDEN_FILES):
            return  # Don't log requests for hidden files
        super().log_message(format, *args)

def run_https_server():
    """Run HTTPS server in a separate thread"""
    try:
        with socketserver.TCPServer((HOST, HTTPS_PORT), SecureHTTPSHandler) as httpd:
            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(CERT_FILE, KEY_FILE)
            
            # Wrap socket with SSL
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            
            print(f"HTTPS Server running on https://localhost:{HTTPS_PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"HTTPS Server error: {e}")

def run_http_server():
    """Run HTTP server in a separate thread"""
    try:
        with socketserver.TCPServer((HOST, HTTP_PORT), SecureHTTPSHandler) as httpd:
            print(f"HTTP Server running on http://localhost:{HTTP_PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"HTTP Server error: {e}")

def run_server():
    # Check if certificate files exist for HTTPS
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print(f"Error: {CERT_FILE} or {KEY_FILE} not found!")
        print("Generate them with:")
        print("python3 ctrl keys")
        return
    
    print("Starting dual HTTP/HTTPS server...")
    print(f"Serving web files from: {os.getcwd()}/public")
    print(f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}")
    print()
    print("Access URLs:")
    print(f"  Landing page: http://localhost:{HTTP_PORT}/")
    print(f"  HTTPS (for mobile browsers): https://localhost:{HTTPS_PORT}/speed.html")
    print(f"  HTTP (for IRL Pro): http://localhost:{HTTP_PORT}/speed.html")
    print()
    print("Certificate Installation:")
    print(f"  Install page: http://localhost:{HTTP_PORT}/install.html")
    print(f"  CA download: http://localhost:{HTTP_PORT}/ca.crt")
    print(f"  Verify page: https://localhost:{HTTPS_PORT}/verify.html")
    print()
    print("Press Ctrl+C to stop both servers")
    
    # Start HTTPS server in a separate thread
    https_thread = threading.Thread(target=run_https_server, daemon=True)
    https_thread.start()
    
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\nStopping both servers...")

def run_daemon():
    """Run dual server as daemon and write PID file"""
    import sys
    
    # Check if certificate files exist
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        sys.exit(1)
    
    # Write PID file
    pid_file = '/tmp/https_server.pid'
    log_file = '/tmp/https_server.log'
    
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Redirect stdout/stderr to log file
    with open(log_file, 'w') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    print(f"Dual HTTP/HTTPS Server daemon started")
    print(f"HTTPS: https://localhost:{HTTPS_PORT}")
    print(f"HTTP: http://localhost:{HTTP_PORT}")
    print(f"Serving web files from: {os.getcwd()}/public")
    print(f"PID: {os.getpid()}")
    
    # Start HTTPS server in a separate thread
    https_thread = threading.Thread(target=run_https_server, daemon=True)
    https_thread.start()
    
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Servers stopped")
    finally:
        # Clean up PID file
        if os.path.exists(pid_file):
            os.unlink(pid_file)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        run_daemon()
    else:
        run_server()
