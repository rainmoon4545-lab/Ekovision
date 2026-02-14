"""
Test script for web dashboard components.
"""
import sys

print("="*60)
print("WEB DASHBOARD COMPONENT TEST")
print("="*60)

# Test 1: Import Flask dependencies
print("\n1. Testing Flask dependencies...")
try:
    import flask
    import flask_socketio
    import socketio
    print("✓ Flask dependencies imported")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Import web dashboard module
print("\n2. Testing web dashboard import...")
try:
    from src.web_dashboard.app import WebDashboard
    print("✓ WebDashboard imported")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 3: Check template file exists
print("\n3. Testing template file...")
try:
    import os
    template_path = "src/web_dashboard/templates/index.html"
    if os.path.exists(template_path):
        print(f"✓ Template file exists: {template_path}")
    else:
        print(f"✗ Template file not found: {template_path}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Template check failed: {e}")
    sys.exit(1)

# Test 4: Check run script exists
print("\n4. Testing run script...")
try:
    run_script = "run_web_dashboard.py"
    if os.path.exists(run_script):
        print(f"✓ Run script exists: {run_script}")
    else:
        print(f"✗ Run script not found: {run_script}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Run script check failed: {e}")
    sys.exit(1)

# Test 5: Test Flask app creation
print("\n5. Testing Flask app creation...")
try:
    from flask import Flask
    from flask_socketio import SocketIO
    
    app = Flask(__name__)
    socketio = SocketIO(app)
    print("✓ Flask app and SocketIO created")
except Exception as e:
    print(f"✗ Flask app creation failed: {e}")
    sys.exit(1)

# Test 6: Check port availability
print("\n6. Testing port availability...")
try:
    import socket
    
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    port = 5000
    if is_port_available(port):
        print(f"✓ Port {port} is available")
    else:
        print(f"⚠ Port {port} is in use (this is OK if dashboard is already running)")
except Exception as e:
    print(f"✗ Port check failed: {e}")

print("\n" + "="*60)
print("WEB DASHBOARD COMPONENT TEST SUMMARY")
print("="*60)
print("✓ All critical components verified")
print("\nTo start the dashboard:")
print("  python run_web_dashboard.py")
print("\nThen open browser:")
print("  http://localhost:5000")
print("="*60)
