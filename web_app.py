"""
Web Interface for Telegram Bot
Modern dashboard for bot management and statistics
"""

import asyncio
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import aiofiles
from database import Database
from config import Config
from utils import Utils

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize configuration
config = Config()
database = Database()

@app.route('/')
def dashboard():
    """Main dashboard"""
    try:
        # Get bot statistics
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
        
        stats = {
            'total_users': total_users,
            'total_urls': total_urls,
            'total_files': total_files,
            'total_clicks': total_clicks,
            'total_storage': Utils.format_file_size(total_storage),
            'recent_urls': recent_urls,
            'recent_files': recent_files
        }
        
        return render_template('dashboard.html', stats=stats)
        
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/urls')
def urls_page():
    """URL management page"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Get all URLs with user info
        cursor.execute("""
            SELECT s.short_code, s.original_url, s.click_count, s.created_date,
                   u.first_name, u.username
            FROM short_urls s
            LEFT JOIN users u ON s.user_id = u.user_id
            ORDER BY s.created_date DESC
            LIMIT 50
        """)
        
        urls = cursor.fetchall()
        conn.close()
        
        return render_template('urls.html', urls=urls)
        
    except Exception as e:
        return f"Error loading URLs: {str(e)}", 500

@app.route('/files')
def files_page():
    """File management page"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Get all files with user info
        cursor.execute("""
            SELECT f.file_name, f.file_size, f.file_type, f.upload_date,
                   u.first_name, u.username, f.file_id
            FROM files f
            LEFT JOIN users u ON f.user_id = u.user_id
            ORDER BY f.upload_date DESC
            LIMIT 50
        """)
        
        files = cursor.fetchall()
        conn.close()
        
        return render_template('files.html', files=files)
        
    except Exception as e:
        return f"Error loading files: {str(e)}", 500

@app.route('/users')
def users_page():
    """User management page"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Get all users with their stats
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.join_date,
                   u.total_files, u.total_urls, u.is_banned
            FROM users u
            ORDER BY u.join_date DESC
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        return render_template('users.html', users=users)
        
    except Exception as e:
        return f"Error loading users: {str(e)}", 500

@app.route('/settings')
def settings_page():
    """Bot settings page"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Get current settings
        cursor.execute("SELECT key, value FROM bot_settings")
        settings_rows = cursor.fetchall()
        
        settings = {}
        for key, value in settings_rows:
            settings[key] = value
            
        conn.close()
        
        return render_template('settings.html', settings=settings)
        
    except Exception as e:
        return f"Error loading settings: {str(e)}", 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for real-time stats"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM short_urls")
        total_urls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(click_count) FROM short_urls")
        total_clicks = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'users': total_users,
            'urls': total_urls,
            'files': total_files,
            'clicks': total_clicks
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_setting', methods=['POST'])
def update_setting():
    """Update bot setting"""
    try:
        key = request.form.get('key')
        value = request.form.get('value')
        
        if not key:
            return jsonify({'error': 'Key is required'}), 400
            
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO bot_settings (key, value, updated_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_url', methods=['POST'])
def delete_url():
    """Delete a shortened URL"""
    try:
        short_code = request.form.get('short_code')
        
        if not short_code:
            return jsonify({'error': 'Short code is required'}), 400
            
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM short_urls WHERE short_code = ?", (short_code,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot_status')
def bot_status():
    """Get bot status"""
    try:
        # Check if bot is running by looking at recent activity
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT created_date FROM short_urls 
            ORDER BY created_date DESC 
            LIMIT 1
        """)
        
        last_activity = cursor.fetchone()
        conn.close()
        
        status = {
            'online': True,
            'last_activity': last_activity[0] if last_activity else 'Never',
            'uptime': '0 days',  # We'll implement proper uptime tracking later
            'version': '2.0',
            'features': {
                'url_shortening': True,
                'file_handling': True,
                'custom_domain': True,
                'api_support': True
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)