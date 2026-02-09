#!/usr/bin/env python3
"""
GENZ4GTM Lovable → Brevo Webhook
Receives form submissions from Lovable and syncs to Brevo automatically
"""

from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
BREVO_API_KEY = "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"
BREVO_API_URL = "https://api.brevo.com/v3/contacts"

# Webhook secret (optional, for security)
WEBHOOK_SECRET = "genz4gtm-webhook-secret-2026"

@app.route('/', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "GENZ4GTM Lovable→Brevo Webhook",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/webhook/lovable-form', methods=['POST'])
def lovable_form_webhook():
    """
    Receives form submissions from Lovable
    Expected JSON payload:
    {
        "fullName": "John Doe",
        "email": "john@example.com",
        "age": 24,
        "roleTypes": ["SDR", "AE"],
        "gtmAreas": ["Sales", "Growth"],
        "cv": "optional-url-or-attachment"
    }
    """
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON payload received"}), 400
        
        # Parse incoming data
        full_name = data.get('fullName', '').strip()
        email = data.get('email', '').strip()
        age = data.get('age')
        role_types = data.get('roleTypes', [])
        gtm_areas = data.get('gtmAreas', [])
        cv_url = data.get('cv', '')
        
        # Validate required fields
        if not email or not full_name:
            return jsonify({
                "error": "Missing required fields: fullName and email"
            }), 400
        
        # Parse name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Format role interest
        role_interest = ', '.join(role_types) if role_types else 'General interest'
        gtm_interest = ', '.join(gtm_areas) if gtm_areas else 'Not specified'
        
        # Prepare Brevo contact payload
        brevo_payload = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "attributes": {
                "ROLE_INTEREST": role_interest,
                "GTM_AREAS": gtm_interest,
                "AGE": int(age) if age else None,
                "CV_URL": cv_url if cv_url else None
            }
        }
        
        # Remove None values
        brevo_payload["attributes"] = {
            k: v for k, v in brevo_payload["attributes"].items() if v is not None
        }
        
        # Send to Brevo
        brevo_response = requests.post(
            BREVO_API_URL,
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json"
            },
            json=brevo_payload,
            timeout=10
        )
        
        # Log the response
        print(f"[{datetime.utcnow().isoformat()}] Form submission received")
        print(f"  Email: {email}")
        print(f"  Name: {full_name}")
        print(f"  Brevo Status: {brevo_response.status_code}")
        
        # Check Brevo response
        if brevo_response.status_code in [201, 204, 400]:
            # 201 = created, 204 = updated, 400 = duplicate (already exists - that's OK)
            return jsonify({
                "status": "success",
                "message": f"Contact {email} synced to Brevo",
                "brevo_code": brevo_response.status_code
            }), 200
        else:
            error_msg = brevo_response.text
            print(f"  ❌ Brevo Error: {error_msg}")
            return jsonify({
                "status": "error",
                "message": "Failed to sync to Brevo",
                "details": error_msg
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Request timeout - Brevo API not responding"
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"Request failed: {str(e)}"
        }), 500
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({
            "error": f"Webhook error: {str(e)}"
        }), 500

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """
    Test endpoint - sends a test contact to Brevo
    """
    test_payload = {
        "fullName": "Test User",
        "email": f"test-{datetime.utcnow().timestamp()}@genz4gtm.test",
        "age": 25,
        "roleTypes": ["SDR"],
        "gtmAreas": ["Sales"]
    }
    
    # Reuse the main webhook logic
    return lovable_form_webhook()

if __name__ == '__main__':
    # Run on port 5000 locally, but Replit/Vercel will assign a port
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
