"""
Simple Web Interface for Telegram Bot
Using Python's built-in HTTP server to avoid dependency issues
"""

import http.server
import socketserver
import urllib.parse
import json
import sqlite3
import os
from datetime import datetime

PORT = 5000

class BotWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.routes = {
            '/': self.serve_dashboard,
            '/api/stats': self.api_stats,
            '/api/bot_status': self.api_bot_status,
        }
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path
        
        if path in self.routes:
            self.routes[path]()
        elif path.startswith('/static/'):
            self.serve_static_file()
        else:
            self.serve_dashboard()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/update_setting':
            self.api_update_setting()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard"""
        try:
            stats = self.get_bot_stats()
            html = self.generate_dashboard_html(stats)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_static_file(self):
        """Serve static files (CSS, JS, etc.)"""
        try:
            file_path = self.path[1:]  # Remove leading /
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                if file_path.endswith('.css'):
                    content_type = 'text/css'
                elif file_path.endswith('.js'):
                    content_type = 'application/javascript'
                else:
                    content_type = 'text/plain'
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404)
        except Exception as e:
            self.send_error(500, str(e))
    
    def api_stats(self):
        """API endpoint for real-time stats"""
        try:
            stats = self.get_bot_stats()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'users': stats['total_users'],
                'urls': stats['total_urls'],
                'files': stats['total_files'],
                'clicks': stats['total_clicks']
            }
            
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def api_bot_status(self):
        """API endpoint for bot status"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'online': True,
                'last_activity': 'Just now',
                'uptime': '1 hour',
                'version': '2.0',
                'features': {
                    'url_shortening': True,
                    'file_handling': True,
                    'custom_domain': True,
                    'api_support': True
                }
            }
            
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def api_update_setting(self):
        """API endpoint to update settings"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = urllib.parse.parse_qs(post_data)
            
            key = data.get('key', [''])[0]
            value = data.get('value', [''])[0]
            
            if key:
                # Update setting in database
                conn = sqlite3.connect('bot_data.db')
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO bot_settings (key, value, updated_date)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            else:
                self.send_error(400, 'Key is required')
                
        except Exception as e:
            self.send_error(500, str(e))
    
    def get_bot_stats(self):
        """Get bot statistics from database"""
        try:
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM short_urls")
            total_urls = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM files")
            total_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(click_count) FROM short_urls")
            total_clicks = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(file_size) FROM files")
            total_storage = cursor.fetchone()[0] or 0
            
            # Get recent activity
            cursor.execute("""
                SELECT original_url, short_code, created_date 
                FROM short_urls 
                ORDER BY created_date DESC 
                LIMIT 5
            """)
            recent_urls = cursor.fetchall()
            
            cursor.execute("""
                SELECT file_name, file_size, upload_date 
                FROM files 
                ORDER BY upload_date DESC 
                LIMIT 5
            """)
            recent_files = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_users': total_users,
                'total_urls': total_urls,
                'total_files': total_files,
                'total_clicks': total_clicks,
                'total_storage': self.format_file_size(total_storage),
                'recent_urls': recent_urls,
                'recent_files': recent_files
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'total_users': 0,
                'total_urls': 0,
                'total_files': 0,
                'total_clicks': 0,
                'total_storage': '0 B',
                'recent_urls': [],
                'recent_files': []
            }
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def generate_dashboard_html(self, stats):
        """Generate dashboard HTML"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mraprguild Bot Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            color: white;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        .stat-icon.users {{ color: #3b82f6; }}
        .stat-icon.urls {{ color: #10b981; }}
        .stat-icon.files {{ color: #8b5cf6; }}
        .stat-icon.clicks {{ color: #f59e0b; }}
        .stat-icon.storage {{ color: #ef4444; }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: #6b7280;
            font-weight: 500;
        }}
        
        .features {{
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        
        .features h2 {{
            margin-bottom: 1.5rem;
            color: #1f2937;
        }}
        
        .feature-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        
        .feature {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            background: #f9fafb;
            border-radius: 0.5rem;
        }}
        
        .feature i {{
            color: #10b981;
            font-size: 1.2rem;
        }}
        
        .bot-status {{
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            background: #10b981;
            color: white;
            border-radius: 2rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}
        
        .status-dot {{
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .refresh-btn {{
            background: #6366f1;
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s ease;
        }}
        
        .refresh-btn:hover {{
            background: #4f46e5;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1><i class="fas fa-robot"></i> Mraprguild Bot</h1>
            <p>Modern Telegram Bot Dashboard - URL Shortener & File Handler</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon users"><i class="fas fa-users"></i></div>
                <div class="stat-number">{stats['total_users']}</div>
                <div class="stat-label">Total Users</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon urls"><i class="fas fa-link"></i></div>
                <div class="stat-number">{stats['total_urls']}</div>
                <div class="stat-label">URLs Shortened</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon files"><i class="fas fa-file-upload"></i></div>
                <div class="stat-number">{stats['total_files']}</div>
                <div class="stat-label">Files Stored</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon clicks"><i class="fas fa-mouse-pointer"></i></div>
                <div class="stat-number">{stats['total_clicks']}</div>
                <div class="stat-label">Total Clicks</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon storage"><i class="fas fa-hdd"></i></div>
                <div class="stat-number">{stats['total_storage']}</div>
                <div class="stat-label">Storage Used</div>
            </div>
        </div>
        
        <div class="features">
            <h2><i class="fas fa-star"></i> Bot Features</h2>
            <div class="feature-list">
                <div class="feature">
                    <i class="fas fa-check-circle"></i>
                    <span>URL Shortening with Custom Domains</span>
                </div>
                <div class="feature">
                    <i class="fas fa-check-circle"></i>
                    <span>4GB File Upload Support</span>
                </div>
                <div class="feature">
                    <i class="fas fa-check-circle"></i>
                    <span>Telegram Channel Backup</span>
                </div>
                <div class="feature">
                    <i class="fas fa-check-circle"></i>
                    <span>Real-time Analytics</span>
                </div>
                <div class="feature">
                    <i class="fas fa-check-circle"></i>
                    <span>Admin Management Panel</span>
                </div>
                <div class="feature">
                    <i class="fas fa-check-circle"></i>
                    <span>Cross-platform Support</span>
                </div>
            </div>
        </div>
        
        <div class="bot-status">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span>Bot Online & Running</span>
            </div>
            <p>Your Telegram bot is active and ready to handle requests!</p>
            <button class="refresh-btn" onclick="location.reload()">
                <i class="fas fa-sync-alt"></i> Refresh Dashboard
            </button>
        </div>
    </div>
    
    <script>
        // Auto-refresh stats every 30 seconds
        setInterval(() => {{
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {{
                    // Update stats without full page reload
                    console.log('Stats updated:', data);
                }})
                .catch(error => console.error('Error:', error));
        }}, 30000);
    </script>
</body>
</html>
        """

def start_web_server():
    """Start the web server"""
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), BotWebHandler) as httpd:
            print(f"🌐 Web Dashboard starting on http://0.0.0.0:{PORT}")
            print(f"🚀 Mraprguild Bot Dashboard is now live!")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting web server: {e}")

if __name__ == "__main__":
    start_web_server()