# Osmosis Download Server
# Simple HTTP server to host the download link

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path
import zipfile
import shutil

class OsmosisDownloadHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/osmosis_download.html'
        elif self.path == '/osmosis_v2.0_complete.zip':
            self.serve_download()
            return
        elif self.path == '/status':
            self.serve_status()
            return
        
        return super().do_GET()
    
    def serve_download(self):
        """Serve the Osmosis download package"""
        package_path = Path("package_output/Osmosis_v2.0_Complete.zip")
        
        if not package_path.exists():
            self.send_error(404, "Package not found. Please run create_package.bat first.")
            return
        
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", "attachment; filename=Osmosis_v2.0_Complete.zip")
        self.send_header("Content-Length", str(package_path.stat().st_size))
        self.end_headers()
        
        with open(package_path, 'rb') as f:
            shutil.copyfileobj(f, self.wfile)
    
    def serve_status(self):
        """Serve status information"""
        dist_path = Path("dist")
        package_path = Path("package_output/Osmosis_v2.0_Complete.zip")
        
        status = {
            "built": dist_path.exists(),
            "packaged": package_path.exists(),
            "package_size": package_path.stat().st_size if package_path.exists() else 0
        }
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        import json
        self.wfile.write(json.dumps(status).encode())

def create_server():
    """Create and start the download server"""
    PORT = 8080
    
    # Ensure we have the necessary files
    if not Path("osmosis_download.html").exists():
        print("❌ Error: osmosis_download.html not found!")
        return
    
    print("🌐 Starting Osmosis Download Server...")
    print(f"📡 Server URL: http://localhost:{PORT}")
    print("📁 Serving from:", os.getcwd())
    print()
    
    # Check if package exists
    package_path = Path("package_output/Osmosis_v2.0_Complete.zip")
    if package_path.exists():
        size_mb = package_path.stat().st_size / (1024 * 1024)
        print(f"📦 Package ready: {package_path.name} ({size_mb:.1f} MB)")
    else:
        print("⚠️  Package not found. Run 'create_package.bat' to create it.")
    
    print("\n" + "="*50)
    print("🚀 OSMOSIS DOWNLOAD SERVER STARTED")
    print("="*50)
    print("Access the download page at:")
    print(f"   → http://localhost:{PORT}")
    print("\nPress Ctrl+C to stop the server")
    print("="*50)
    
    try:
        with socketserver.TCPServer(("", PORT), OsmosisDownloadHandler) as httpd:
            # Open browser automatically
            webbrowser.open(f"http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"❌ Error: Port {PORT} is already in use!")
            print("Try closing other applications or use a different port.")
        else:
            print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    create_server()
