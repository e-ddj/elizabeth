#!/usr/bin/env python3
"""
Test script for the new user-to-jobs matching endpoint.

Usage:
    python tests/test_user_matching_endpoint.py [user_id]
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:5004")
ENDPOINT = f"{BASE_URL}/api/job-matcher/match-user"

def test_user_matching(user_id: str, overwrite: bool = False):
    """Test the user matching endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing User-to-Jobs Matching Endpoint")
    print(f"{'='*60}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Endpoint: {ENDPOINT}")
    print(f"User ID: {user_id}")
    print(f"Overwrite existing: {overwrite}")
    print(f"{'='*60}\n")
    
    # Prepare request payload
    payload = {
        "user_id": user_id,
        "overwrite_existing_matches": overwrite
    }
    
    # Make the request
    try:
        print(f"Sending POST request to {ENDPOINT}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Parse response
        if response.status_code == 202:
            data = response.json()
            print(f"\n✅ SUCCESS - Matching process started")
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"\nThe matching process is running asynchronously.")
            print(f"Check the 'match' table in Supabase for results.")
        elif response.status_code == 404:
            print(f"\n❌ ERROR - User not found")
            print(f"Response: {response.text}")
        elif response.status_code == 400:
            print(f"\n❌ ERROR - Bad request")
            print(f"Response: {response.text}")
        else:
            print(f"\n❌ ERROR - Unexpected response")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR - Could not connect to {ENDPOINT}")
        print("Make sure the job-matcher service is running.")
    except Exception as e:
        print(f"\n❌ ERROR - {type(e).__name__}: {str(e)}")

def main():
    """Main function."""
    # Get user ID from command line or use a default
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        # Example user ID - replace with an actual user ID from your database
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        print(f"No user ID provided. Using example: {user_id}")
    
    # Test the endpoint
    test_user_matching(user_id)
    
    # Optionally test with overwrite flag
    if len(sys.argv) > 2 and sys.argv[2] == "--overwrite":
        print("\n" + "="*60)
        print("Testing with overwrite_existing_matches=True")
        test_user_matching(user_id, overwrite=True)

if __name__ == "__main__":
    main()