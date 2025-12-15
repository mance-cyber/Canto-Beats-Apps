"""
Canto-beats License Server
Online license verification API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import time
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_PATH = Path(__file__).parent / "licenses.db"
MAX_MACHINES_DEFAULT = 2

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create licenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            license_type TEXT DEFAULT 'permanent',
            max_machines INTEGER DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email TEXT,
            notes TEXT
        )
    """)
    
    # Create activations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_id INTEGER NOT NULL,
            machine_fingerprint TEXT NOT NULL,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (license_id) REFERENCES licenses(id),
            UNIQUE(license_id, machine_fingerprint)
        )
    """)
    
    conn.commit()
    conn.close()

@app.route('/api/v1/activate', methods=['POST'])
def activate_license():
    """
    Activate a license on a machine
    
    Request body:
    {
        "license_key": "XXXX-XXXX-XXXX-XXXX",
        "machine_fingerprint": "abc123..."
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Invalid request"}), 400
    
    license_key = data.get('license_key', '').strip().upper()
    machine_fingerprint = data.get('machine_fingerprint', '').strip()
    
    if not license_key or not machine_fingerprint:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Find license
        cursor.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,))
        license_row = cursor.fetchone()
        
        if not license_row:
            # Auto-register new license (for flexibility)
            cursor.execute(
                "INSERT INTO licenses (license_key, max_machines) VALUES (?, ?)",
                (license_key, MAX_MACHINES_DEFAULT)
            )
            conn.commit()
            cursor.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,))
            license_row = cursor.fetchone()
        
        license_id = license_row['id']
        max_machines = license_row['max_machines']
        
        # Check existing activations
        cursor.execute(
            "SELECT * FROM activations WHERE license_id = ? AND is_active = 1",
            (license_id,)
        )
        activations = cursor.fetchall()
        
        # Check if this machine is already activated
        for act in activations:
            if act['machine_fingerprint'] == machine_fingerprint:
                # Update last verified time
                cursor.execute(
                    "UPDATE activations SET last_verified_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (act['id'],)
                )
                conn.commit()
                return jsonify({
                    "success": True,
                    "message": "授權有效",
                    "machines_used": len(activations),
                    "machines_allowed": max_machines,
                    "already_activated": True
                })
        
        # Check if max machines reached
        if len(activations) >= max_machines:
            return jsonify({
                "success": False,
                "message": f"已達機器數量上限 ({max_machines} 台)",
                "machines_used": len(activations),
                "machines_allowed": max_machines
            }), 403
        
        # Activate on new machine
        cursor.execute(
            "INSERT INTO activations (license_id, machine_fingerprint) VALUES (?, ?)",
            (license_id, machine_fingerprint)
        )
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "授權成功！",
            "machines_used": len(activations) + 1,
            "machines_allowed": max_machines
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/verify', methods=['POST'])
def verify_license():
    """
    Verify license status
    
    Request body:
    {
        "license_key": "XXXX-XXXX-XXXX-XXXX",
        "machine_fingerprint": "abc123..."
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Invalid request"}), 400
    
    license_key = data.get('license_key', '').strip().upper()
    machine_fingerprint = data.get('machine_fingerprint', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Find license
        cursor.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,))
        license_row = cursor.fetchone()
        
        if not license_row:
            return jsonify({"success": False, "message": "序號不存在"}), 404
        
        license_id = license_row['id']
        
        # Check if this machine is activated
        cursor.execute(
            """SELECT * FROM activations 
               WHERE license_id = ? AND machine_fingerprint = ? AND is_active = 1""",
            (license_id, machine_fingerprint)
        )
        activation = cursor.fetchone()
        
        if not activation:
            return jsonify({"success": False, "message": "此機器未授權"}), 403
        
        # Update last verified time
        cursor.execute(
            "UPDATE activations SET last_verified_at = CURRENT_TIMESTAMP WHERE id = ?",
            (activation['id'],)
        )
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "授權有效",
            "license_type": license_row['license_type'],
            "activated_at": activation['activated_at']
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/deactivate', methods=['POST'])
def deactivate_license():
    """
    Deactivate a machine
    
    Request body:
    {
        "license_key": "XXXX-XXXX-XXXX-XXXX",
        "machine_fingerprint": "abc123..."
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Invalid request"}), 400
    
    license_key = data.get('license_key', '').strip().upper()
    machine_fingerprint = data.get('machine_fingerprint', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM licenses WHERE license_key = ?", (license_key,))
        license_row = cursor.fetchone()
        
        if not license_row:
            return jsonify({"success": False, "message": "序號不存在"}), 404
        
        cursor.execute(
            """UPDATE activations SET is_active = 0 
               WHERE license_id = ? AND machine_fingerprint = ?""",
            (license_row['id'], machine_fingerprint)
        )
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "已解除授權"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# Initialize database on startup
init_db()

if __name__ == '__main__':
    print("Starting Canto-beats License Server...")
    print(f"Database: {DATABASE_PATH}")
    app.run(host='0.0.0.0', port=5000, debug=True)
