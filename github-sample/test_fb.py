#!/usr/bin/env python3
"""
Simple script to test Facebook Page API connection and posting.
"""
import os
import sys
import requests
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

if not PAGE_ID or not PAGE_TOKEN:
    print("❌ Error: FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN is missing in .env")
    sys.exit(1)

def verify_page():
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}"
    params = {
        "fields": "id,name,fan_count,link",
        "access_token": PAGE_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if response.status_code == 200:
        print("✅ Facebook Connection Successful!")
        print(f"   • Page Name: {data.get('name')}")
        print(f"   • Page ID: {data.get('id')}")
        print(f"   • Followers/Likes: {data.get('fan_count', 0)}")
        return True
    else:
        print("❌ Facebook API Error:")
        print(data)
        return False

def test_post(message="🚀 Test post from automated Telegram poster system!"):
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": PAGE_TOKEN
    }
    response = requests.post(url, data=payload)
    data = response.json()
    
    if response.status_code == 200:
        post_id = data.get("id")
        print("🎉 Post published successfully to Facebook!")
        print(f"   • Post ID: {post_id}")
        return post_id
    else:
        print("❌ Failed to publish post:")
        print(data)
        return None

if __name__ == "__main__":
    print(f"Testing connection to Facebook Page ({PAGE_ID})...")
    if verify_page():
        if "--post" in sys.argv:
            print("\nPublishing a test post to page...")
            test_post()
        else:
            print("\nRun with --post to publish a test status update:")
            print("  python test_fb.py --post")
