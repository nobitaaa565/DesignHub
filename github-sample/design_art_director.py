#!/usr/bin/env python3
"""
Design Hub Autonomous Creative Art Director
Maps user requests and campaign topics into one of the 5 official design archive archetypes
and enriches diffusion prompts with exact lighting, materials, and composition.
"""

import os
import re
import io
import json
import logging
from pathlib import Path
from PIL import Image
import requests
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

logger = logging.getLogger("ArtDirector")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LOGO_PATH = Path(__file__).resolve().parent / "designuhb-logo.png"

ARCHIVE_STYLES = {
    "design-1_reference": {
        "name": "Design 1: Clean & Bright Studio Character",
        "folder": "designs/design-1_reference",
        "description": "High-key ivory-white daylight studio, friendly 3D Pixar-style creative character, dashed discount coupon box, trust pills, soft contact floor shadows.",
        "keywords": ["student", "beginner", "learner", "easy", "friendly", "walkthrough", "trust", "access first pay later", "motivation", "starter", "simple", "daily", "25tk", "25 tk"]
    },
    "design-2_reference": {
        "name": "Design 2: Atmospheric Dark Mode & Floating 3D Elements",
        "folder": "designs/design-2_reference",
        "description": "Deep obsidian/navy background, glowing cyan (#00C4CC) and purple (#7D2AE8) rim lights, floating 3D Canva squircle tile, floating 'Aa' glyphs, color swatches, sleek horizontal frosted-glass dock card.",
        "keywords": ["pro designer", "agency", "advanced", "dark mode", "modern tech", "all-in-one", "magic studio", "creative tools", "night owl", "speed", "unlimited", "50 tk", "50tk", "3 months"]
    },
    "design-3_reference": {
        "name": "Design 3: Ultra-Premium Glassmorphism Pricing Tiles",
        "folder": "designs/design-3_reference",
        "description": "Overhead dramatic cinematic spotlight, three floating frosted-glass cards side-by-side with 1px specular beveled rims, elevated center hero card with gold 'Best Value' star badge, luxury floor reflections.",
        "keywords": ["pricing", "packages", "comparison", "plans", "1 month", "3 months", "6 months", "discount", "flash sale", "best value", "save money", "upgrade", "tier", "99tk", "99 tk", "150tk"]
    },
    "design-4_reference": {
        "name": "Design 4: Poetic Conceptual Art & Physical Metaphor",
        "folder": "designs/design-4_reference",
        "description": "Directional museum lighting on matte Prussian-blue or graphite surface. Tangible tool beside 3D Canva token, drawn line morphing into luminous ribbon of frosted colored glass, condensed ivory headline with amber pill badge.",
        "keywords": ["anyone can create", "creativity", "imagination", "artistic metaphor", "storytelling", "brand empowerment", "craft", "thought leadership", "pencil to digital", "transformation", "ideas"]
    },
    "design-5_reference": {
        "name": "Design 5: National & Observance Day Vector Art",
        "folder": "designs/design-5_reference",
        "description": "Dignified modern layered vector illustration with smooth shading, Bangladesh national flag, National Monument (Smriti Soudho), water lilies, united citizens, calendar date badge, zero commercial selling.",
        "keywords": ["independence day", "victory day", "21 february", "language movement", "ekushey", "shadhinota", "bijoy", "revolution", "national day", "eid", "pohela boishakh", "cultural", "tribute"]
    }
}


def rule_based_fallback(user_prompt: str) -> dict:
    """Fallback classifier when AI API is unavailable."""
    lower = user_prompt.lower()

    if any(k in lower for k in ARCHIVE_STYLES["design-5_reference"]["keywords"]):
        arch_id = "design-5_reference"
    elif any(k in lower for k in ARCHIVE_STYLES["design-3_reference"]["keywords"]) or "99" in lower:
        arch_id = "design-3_reference"
    elif any(k in lower for k in ARCHIVE_STYLES["design-4_reference"]["keywords"]) or "concept" in lower or "inspire" in lower:
        arch_id = "design-4_reference"
    elif any(k in lower for k in ARCHIVE_STYLES["design-2_reference"]["keywords"]) or "50" in lower or "pro" in lower or "dark" in lower:
        arch_id = "design-2_reference"
    else:
        arch_id = "design-1_reference"

    style = ARCHIVE_STYLES[arch_id]
    enriched = (
        f"1080x1350 portrait ultra-clean commercial advertising poster. "
        f"Aspect ratio 4:5 vertical (1080x1350 px). "
        f"Style: {style['description']}. "
        f"Subject theme: {user_prompt}. "
        f"Vibrant brand colors (cyan, royal purple, warm amber accents), clean composition with top-left area clear for logo placement, 8k resolution, cinematic lighting."
    )
    caption = f"✨ Transform your workflow with Design Hub! Get official Canva Pro access today.\n\n#DesignHub #CanvaPro #CreativeTools"
    return {
        "archetype_id": arch_id,
        "archetype_name": style["name"],
        "reason": f"Matched context keywords from {arch_id} archive DNA.",
        "enriched_prompt": enriched,
        "caption": caption
    }


def evaluate_and_enrich_prompt(user_prompt: str) -> dict:
    """Uses Gemini 3.5 Flash as the Art Director to evaluate context and synthesize the enriched prompt."""
    if not GEMINI_API_KEY:
        return rule_based_fallback(user_prompt)

    system_instruction = (
        "You are the Executive Creative Art Director for 'Design Hub', a premier Bangladeshi creative brand.\n"
        "Your role: Analyze the user's campaign request and autonomously pick the SINGLE best matching design archetype "
        "from the 5 official archive references:\n\n"
        "1. 'design-1_reference': Clean & Bright Studio Character (High-key daylight, friendly 3D Pixar-style character, dashed coupon box, ideal for students, beginners, 25tk offers, high-trust walkthroughs)\n"
        "2. 'design-2_reference': Atmospheric Dark Mode & Floating 3D Elements (Deep obsidian background, electric cyan/purple rim lights, floating 3D Canva squircle tile, floating typography glyphs & swatches, glass dock, ideal for pro designers, tech tools, 50tk / 3-month deals)\n"
        "3. 'design-3_reference': Ultra-Premium Glassmorphism Pricing Tiles (Overhead dramatic spotlight, 3 floating frosted-glass cards with metallic beveled rims, elevated center hero card with gold star badge, ideal for tier comparisons, 99tk 6-month packages, flash sales)\n"
        "4. 'design-4_reference': Poetic Conceptual Art & Physical Metaphor (Matte Prussian-blue/graphite wall, wooden pencil beside 3D Canva token, drawn line morphing into luminous frosted glass ribbon/origami blossom guided by a hand, condensed headline with amber price pill, ideal for brand thought leadership, 'Anyone Can Create', creative empowerment)\n"
        "5. 'design-5_reference': National & Observance Day Vector Art (Layered vector illustration, Bangladesh national flag, National Monument, heroic united citizens, calendar date badge, strictly ZERO commercial selling/no pricing, ideal for Independence Day, Victory Day, Eid, cultural celebrations)\n\n"
        "STRICT INSTRUCTIONS:\n"
        "- Do NOT clone the reference image; take its visual DNA (lighting, mood, materials, geometry) and create a fresh, unique contextual poster for this user request.\n"
        "- The poster MUST be 4:5 vertical portrait format (1080x1350 px).\n"
        "- Keep the top-left corner clean for the company logo.\n"
        "- Output strictly valid JSON matching this schema:\n"
        "{\n"
        '  "archetype_id": "design-1_reference" | "design-2_reference" | "design-3_reference" | "design-4_reference" | "design-5_reference",\n'
        '  "archetype_name": "Full Style Name",\n'
        '  "reason": "1-sentence why this archive archetype was chosen based on user context",\n'
        '  "enriched_prompt": "Ultra-detailed, highly descriptive diffusion prompt incorporating lighting, composition, 3D assets, and color harmony",\n'
        '  "caption": "2-sentence punchy Facebook caption with 3 hashtags"\n'
        "}"
    )

    models = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.8-flash"]
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"User Campaign Request: '{user_prompt}'\n\nAnalyze and provide art direction JSON."}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json"
        }
    }

    for m in ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.8-flash"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                parsed = json.loads(raw_text)
                if "archetype_id" in parsed and "enriched_prompt" in parsed:
                    return parsed
        except Exception as e:
            logger.error(f"Error calling Gemini Art Director ({m}): {e}")

    return rule_based_fallback(user_prompt)


def composite_brand_logo(image_bytes: bytes) -> bytes:
    """
    Fits the generated image into exact 1080x1350 (4:5) Facebook Portrait
    and composites the official transparent Design Hub logo in the top-left corner.
    """
    if not image_bytes or len(image_bytes) < 1000:
        return image_bytes

    try:
        raw = Image.open(io.BytesIO(image_bytes))
        rw, rh = raw.size

        # Fit into 1080x1350 (4:5)
        target_w, target_h = 1080, 1350
        target_ratio = target_w / target_h
        raw_ratio = rw / rh

        if abs(raw_ratio - target_ratio) < 0.05:
            canvas = raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
        else:
            # Crop to center 4:5
            if raw_ratio > target_ratio:
                # Wider than 4:5
                new_w = int(rh * target_ratio)
                left = (rw - new_w) // 2
                canvas = raw.crop((left, 0, left + new_w, rh)).resize((target_w, target_h), Image.Resampling.LANCZOS)
            else:
                # Taller than 4:5
                new_h = int(rw / target_ratio)
                top = (rh - new_h) // 2
                canvas = raw.crop((0, top, rw, top + new_h)).resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Composite logo if exists
        if LOGO_PATH.exists():
            logo_raw = Image.open(LOGO_PATH).convert("RGBA")
            bbox = logo_raw.getbbox()
            if bbox:
                logo_cropped = logo_raw.crop(bbox)
                logo_w = int(target_w * 0.14)
                logo_h = int(logo_w * (logo_cropped.height / logo_cropped.width))
                logo_resized = logo_cropped.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

                logo_x = int(target_w * 0.055)
                logo_y = int(target_h * 0.05)

                canvas_rgba = canvas.convert("RGBA")
                canvas_rgba.paste(logo_resized, (logo_x, logo_y), logo_resized)
                canvas = canvas_rgba.convert("RGB")

        out = io.BytesIO()
        canvas.save(out, format="JPEG", quality=95)
        return out.getvalue()
    except Exception as e:
        logger.error(f"Error compositing logo: {e}")
        return image_bytes


if __name__ == "__main__":
    test_cases = [
        "Canva Pro 25tk offer for university students and beginners",
        "50tk 3 months Canva Pro all in one tools for pro designers",
        "Packages price comparison: 1 month 25tk, 3 months 50tk, 6 months 99tk",
        "Anyone can create: how ideas transform into digital design",
        "Happy Independence Day of Bangladesh celebration"
    ]
    for q in test_cases:
        res = evaluate_and_enrich_prompt(q)
        print(f"\n==========================================")
        print(f"QUERY: {q}")
        print(f"ARCHETYPE: {res.get('archetype_name')}")
        print(f"REASON: {res.get('reason')}")
        print(f"CAPTION: {res.get('caption')}")
        print(f"PROMPT PREVIEW: {res.get('enriched_prompt')[:120]}...")
