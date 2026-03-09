import frappe
from frappe import _
from werkzeug.wrappers import Response

def handle_cors():
    """Handle CORS preflight requests"""
    if frappe.request and frappe.request.method == "OPTIONS":
        # Handle preflight OPTIONS request
        response = Response()
        response.data = {"message": "OK"}
        response.status_code = 200
        add_cors_headers(response)
        frappe.local.response = response
        return response


def add_cors_headers(response=None):
    """Add CORS headers to all responses"""
    if not response:
        return
    
    # Ensure headers object exists
    if not hasattr(response, 'headers') or response.headers is None:
        response.headers = frappe._dict()
    
    # Get the origin from the request
    origin = frappe.get_request_header("Origin", "*")
    
    # Allow requests from localhost and common development ports during development
    allowed_origins = [
        "http://localhost:4321",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080", 
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:4321",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173"
        "http://frappe.localhost:8000",
        "http://frappe.localhost:8080",
        "http://frappe.remotehost:8000",
        "http://frappe.remotehost:8080"
    ]
    
    # In production, you should specify your actual domain(s)
    # For now, we'll allow common development origins and the requesting origin
    if origin in allowed_origins or frappe.conf.get("developer_mode"):
        cors_origin = origin
    else:
        # In production, be more restrictive
        cors_origin = "*"  # Change this to your actual domain in production
    
    # Set CORS headers
    response.headers.add("Access-Control-Allow-Origin", cors_origin)
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Frappe-CSRF-Token, X-Requested-With")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Max-Age", "86400")  # 24 hours
