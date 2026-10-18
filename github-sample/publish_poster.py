#!/usr/bin/env python3
"""
Direct Facebook Poster Publisher for Design Hub
Publishes any poster artwork directly to Design Hub's Facebook Page feed.
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def generate_caption_for_poster(poster_path: str, context_hint: str = "") -> str:
    """Uses Gemini to generate an engaging, high-converting Facebook caption."""
    if not GEMINI_API_KEY:
        return "✨ Transform your workflow with Design Hub! Official Canva Pro access.\n\n#DesignHub #CanvaPro #CreativeTools"

    filename = Path(poster_path).name
    prompt = (
        f"You are the social media manager for 'Design Hub', a Facebook page providing official Canva Pro access in Bangladesh.\n"
        f"Write an engaging, punchy Facebook post caption for this newly created poster: '{filename}'.\n"
        f"Additional context: {context_hint or 'Official Canva Pro license, instant activation, 24/7 support'}.\n"
        f"Include a catchy hook, 2-3 value bullet points, a clear Call to Action (e.g. 'Inbox us now to get access'), and 3-5 relevant hashtags.\n"
        f"Keep it authentic and natural (Bangla or Bengali-English mix)."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 600}
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Warning: Could not generate AI caption: {e}")

    return "✨ আপনার ক্রিয়েটিভ ডিজাইন জার্নিকে আরও সহজ করতে Design Hub দিচ্ছে ১০০% অফিসিয়াল Canva Pro লাইসেন্স! এখনই ইনবক্স করুন।\n\n#DesignHub #CanvaPro #GraphicDesignBD"


def publish_poster(image_path: str, caption: str = "") -> bool:
    """Publishes a local image file to the Facebook Page."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        print("❌ Error: FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN missing in .env")
        return False

    img_file = Path(image_path)
    if not img_file.exists():
        print(f"❌ Error: Image file '{image_path}' not found.")
        return False

    print(f"🚀 Publishing '{img_file.name}' to Facebook Page ({FB_PAGE_ID})...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"

    with open(img_file, "rb") as f:
        files = {"source": (img_file.name, f, "image/jpeg")}
        data = {
            "access_token": FB_PAGE_ACCESS_TOKEN,
            "caption": caption
        }
        res = requests.post(url, data=data, files=files, timeout=40)

    try:
        res_data = res.json()
        if res.status_code == 200 and "id" in res_data:
            post_id = res_data.get("post_id") or res_data.get("id")
            print("=" * 60)
            print("🎉 POST PUBLISHED SUCCESSFULLY TO FACEBOOK!")
            print(f"• Photo ID: {res_data.get('id')}")
            print(f"• Post URL: https://facebook.com/{post_id}")
            print("=" * 60)
            return True
        else:
            print("❌ Facebook API Error:")
            print(res_data)
            return False
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Publish a poster from designs/ to Design Hub Facebook Page")
    parser.add_argument("image", help="Path to image file (e.g. designs/design-2_reference/autonomous_campaign_promo_1080x1350.jpg)")
    parser.add_argument("--caption", "-c", help="Custom caption. If omitted, Gemini AI writes one automatically.")
    parser.add_argument("--hint", "-t", help="Context hint for AI caption (e.g. '50tk 3 months offer')")

    args = parser.parse_args()

    caption = args.caption
    if not caption:
        print("✍️ Generating high-converting Facebook caption with Gemini...")
        caption = generate_caption_for_poster(args.image, args.hint)
        print("\n--- Preview Caption ---")
        print(caption)
        print("-----------------------\n")

    publish_poster(args.image, caption)


if __name__ == "__main__":
    main()
