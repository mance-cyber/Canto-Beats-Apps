"""
Test script for License Distribution Server
Run this to verify everything is working
"""

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"
ADMIN_AUTH = ("admin", "your_password")  # Change this


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_manual_license_generation(email: str, name: str):
    """Test manual license generation"""
    print_section("Testing Manual License Generation")
    
    url = f"{BASE_URL}/admin/generate-license"
    params = {
        "customer_email": email,
        "customer_name": name
    }
    
    response = requests.post(url, params=params, auth=ADMIN_AUTH)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ License generated: {data.get('license_key')}")
        print(f"{'✅' if data.get('email_sent') else '❌'} Email sent")
        return data.get('license_key')
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_list_licenses():
    """Test listing licenses"""
    print_section("Testing List Licenses")
    
    response = requests.get(f"{BASE_URL}/admin/licenses", auth=ADMIN_AUTH)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total licenses: {data.get('total')}")
        
        for lic in data.get('licenses', [])[:5]:  # Show first 5
            print(f"\n  License: {lic.get('license_key')}")
            print(f"  Email: {lic.get('customer_email')}")
            print(f"  Status: {lic.get('status')}")
    else:
        print(f"❌ Failed: {response.text}")


def test_stats():
    """Test statistics endpoint"""
    print_section("Testing Statistics")
    
    response = requests.get(f"{BASE_URL}/admin/stats", auth=ADMIN_AUTH)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"\n📊 System Statistics:")
        print(f"\nLicenses:")
        print(f"  Total: {stats['licenses']['total']}")
        print(f"  Active: {stats['licenses']['active']}")
        print(f"  Used: {stats['licenses']['used']}")
        
        print(f"\nOrders:")
        print(f"  Total: {stats['orders']['total']}")
        print(f"  Completed: {stats['orders']['completed']}")
        print(f"  Failed: {stats['orders']['failed']}")
        
        print(f"\nEmails:")
        print(f"  Total: {stats['emails']['total']}")
        print(f"  Sent: {stats['emails']['sent']}")
        print(f"  Failed: {stats['emails']['failed']}")
    else:
        print(f"❌ Failed: {response.text}")


def main():
    """Run all tests"""
    print("\n🧪 License Distribution Server Test Suite")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ Server is not running or unhealthy")
        print("Please start the server with: python main.py")
        return
    
    # Test 2: Statistics
    test_stats()
    
    # Test 3: List Licenses
    test_list_licenses()
    
    # Test 4: Manual License Generation (optional)
    print("\n" + "="*60)
    generate = input("\nGenerate a test license? (y/n): ").lower()
    
    if generate == 'y':
        email = input("Enter test email: ").strip()
        name = input("Enter test name (optional): ").strip()
        
        if email:
            license_key = test_manual_license_generation(email, name)
            
            if license_key:
                print(f"\n✅ Test completed successfully!")
                print(f"\nGenerated license key: {license_key}")
                print(f"Check your email ({email}) for the license email.")
    
    print("\n" + "="*60)
    print("🎉 All tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
