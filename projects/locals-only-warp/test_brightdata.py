import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def test_brightdata_api():
    """Test BrightData API endpoints and discover available datasets"""
    api_key = os.getenv('BRIGHTDATA_API_KEY')
    
    if not api_key:
        print("❌ No BrightData API key found")
        return
    
    print(f"🔑 Testing BrightData API with key: {api_key[:20]}...")
    
    # Test various BrightData endpoints
    base_urls = [
        "https://api.brightdata.com/dataset",
        "https://api.brightdata.com/datasets",
        "https://api.brightdata.com/v1",
        "https://api.brightdata.com",
        "https://brightdata.com/api",
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'LocalsOnly/1.0'
    }
    
    for base_url in base_urls:
        try:
            print(f"\n🌐 Testing endpoint: {base_url}")
            response = requests.get(base_url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ SUCCESS! Response: {json.dumps(data, indent=2)[:500]}...")
                    return base_url, data
                except:
                    print(f"Response text: {response.text[:200]}...")
            else:
                print(f"Error response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Try different authentication methods
    print("\n🔐 Testing different auth methods...")
    
    alt_headers = [
        {'X-API-Key': api_key},
        {'apikey': api_key},
        {'api-key': api_key},
    ]
    
    for headers in alt_headers:
        try:
            response = requests.get("https://api.brightdata.com", headers=headers, timeout=10)
            print(f"Auth method {headers}: {response.status_code}")
            if response.status_code != 404:
                print(f"Response: {response.text[:100]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_brightdata_api()
