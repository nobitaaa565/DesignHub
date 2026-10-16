#!/usr/bin/env python3
"""
Design Hub - Dedicated Studio Poster Generator Bot
Telegram Bot: @designposterbot
Runs natively on macOS in the background to:
1. Browse and showcase all 7 Design Reference Archetypes sequentially (/designs)
2. Generate promotional posters using Google Imagen 3 / Gemini Image models (/create)
3. Automatically format images to 4:5 Facebook Portrait (1080x1350)
4. Programmatically composite the official transparent Design Hub brand logo
5. 1-Tap Publish directly to Design Hub's Facebook Page
"""

import os
import sys
import time
import json
import asyncio
import logging
import base64
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    BotCommand,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load environment
WORKSPACE_DIR = Path(__file__).resolve().parent
load_dotenv(WORKSPACE_DIR / ".env")

STUDIO_BOT_TOKEN = os.getenv("STUDIO_BOT_TOKEN") or "8948969587:AAFCqGJDH2qG_En5szzPAfqJ6jxl5pFpbow"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")
LOGO_PATH = WORKSPACE_DIR / "designuhb-logo.png"
GENERATED_DIR = WORKSPACE_DIR / "designs" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("StudioBot")

# All 7 Design Archetypes in folder sequence
DESIGNS = [
    {
        "id": 1,
        "name": "Style 1: Clean & Bright Studio Character",
        "folder": "designs/design-1_reference",
        "image": "designs/design-1_reference/sample_poster.jpg",
        "headline": "Daylight Studio & Friendly 3D Creator",
        "dna": "Soft ivory daylight studio, friendly 3D designer character with stylus, dashed discount coupon box, clear trust badges.",
        "triggers": "Beginners, student deals, friendly walkthroughs, 'Access First, Pay Later'.",
        "geometry": "Reverse Split / Character Right (1080x1350)",
    },
    {
        "id": 2,
        "name": "Style 2: Atmospheric Dark Mode & Floating 3D Elements",
        "folder": "designs/design-2_reference",
        "image": "designs/design-2_reference/dynamic_horizontal_promo_1080x1350.jpg",
        "headline": "Cyber Obsidian & Floating 3D Creative Tools",
        "dna": "Deep obsidian navy, neon cyan/purple rim lighting, floating 3D creative assets (swatches, typography, stylus), frosted-glass bottom dock.",
        "triggers": "Feature launches, pro designers, all-in-one suite, modern tech appeal.",
        "geometry": "Top Headline & Bottom Dock (1080x1350)",
    },
    {
        "id": 3,
        "name": "Style 3: Ultra-Premium Glassmorphism Pricing Tiles",
        "folder": "designs/design-3_reference",
        "image": "designs/design-3_reference/reference.jpg",
        "headline": "Spotlight & 3-Card Frosted Glass Comparison",
        "dna": "Dramatic overhead studio spotlight, 3 floating frosted-glass cards with elevated center hero card, centered brand floor.",
        "triggers": "Direct sales, plan upgrades, tier comparisons, flash discounts.",
        "geometry": "3-Card Floor Spotlight (1080x1080)",
    },
    {
        "id": 4,
        "name": "Style 4: Poetic Conceptual Art & Physical Metaphor",
        "folder": "designs/design-4_reference",
        "image": "designs/design-4_reference/canva_conceptual_promo_1080x1350.jpg",
        "headline": "Physical Tool to Glowing Glass Ribbon",
        "dna": "Fine-art physical pencil transforming into a sweeping luminous ribbon of frosted colored glass, ending in glowing origami.",
        "triggers": "Creative empowerment, brand storytelling, intellectual luxury.",
        "geometry": "Centered Gallery Minimalist (1080x1350)",
    },
    {
        "id": 5,
        "name": "Style 5: National & Observance Day Vector Art",
        "folder": "designs/design-5_reference",
        "image": "designs/design-5_reference/national_revolution_and_solidarity_day_celebration.jpg",
        "headline": "Bangladesh National Day Vector Art",
        "dna": "Handcrafted patriotic vector art, national flag elements, dynamic skyline silhouettes, zero commercial selling.",
        "triggers": "National days, victory day, independence day, solidarity day.",
        "geometry": "Patriotic Vector Hierarchy (1080x1350)",
    },
    {
        "id": 6,
        "name": "Style 6: Real Model & Floating 3D Feature Badges",
        "folder": "designs/design-6_reference",
        "image": "designs/design-6_reference/canva_pro_mobile_promo_1080x1350.jpg",
        "headline": "Charismatic Model, Smartphone & 4 Orbiting App Tiles",
        "dna": "Photographic human creator holding smartphone with live UI, 4 orbiting 3D squircle tiles (Canva, AI Wand, 100M+ Assets, Fonts), neon portal aperture.",
        "triggers": "Direct mobile subscription checkout, bKash/Nagad campaigns, student creator promos.",
        "geometry": "Real Model & Orbiting App Tiles (1080x1350)",
    },
    {
        "id": 7,
        "name": "Style 7: Premium SaaS Split-Bento & Feature Stack Grid",
        "folder": "designs/design-7_reference",
        "image": "designs/design-7_reference/canva_pro_bento_promo_1080x1350.jpg",
        "headline": "Split Bento Grid, Stacked Features & Unique Price Ticket",
        "dna": "Vibrant gradient hero card with 3D crown, stark-white embossed ticket badge with unmissable price [ মাত্র ৫০ টাকা ], 5 white feature micro-cards, bottom trust bar.",
        "triggers": "Multi-feature pro breakdown, clear price-point campaigns, high-trust Bangladeshi audience.",
        "geometry": "Split-Bento Hero Card & Feature Stack (1080x1350)",
    },
]


def check_auth(update: Update) -> bool:
    """Verifies that the caller is authorized."""
    user = update.effective_user
    if not user:
        return False
    if ALLOWED_USER_ID and str(user.id) != str(ALLOWED_USER_ID):
        return False
    return True


# =====================================================================
# MAC POST-PROCESSING: 1080x1350 & LOGO COMPOSITING
# =====================================================================

def post_process_poster(raw_image_path: Path, output_image_path: Path, style_id: int) -> Path:
    """
    Takes raw image from AI generator, scales cleanly to 1080x1350 (4:5 Facebook Portrait)
    or 1080x1080 for Style 3, patches any AI placeholder, and composites designuhb-logo.png.
    """
    img = Image.open(raw_image_path).convert("RGB")
    w, h = img.size

    # Style 3 is square (1080x1080), all others are 4:5 Facebook Portrait (1080x1350)
    target_w, target_h = (1080, 1080) if style_id == 3 else (1080, 1350)

    # Clean top-left logo area (patch placeholder text like 'Logo Overlay' or generic artifact)
    if style_id != 3:
        # Patch top-left box
        draw = ImageDraw.Draw(img)
        c_top = img.getpixel((min(w - 1, 100), 15))
        c_bot = img.getpixel((min(w - 1, 100), min(h - 1, 115)))
        for y in range(15, min(h - 1, 120)):
            t = (y - 15) / max(1, 120 - 15)
            r = int(c_top[0] * (1 - t) + c_bot[0] * t)
            g = int(c_top[1] * (1 - t) + c_bot[1] * t)
            b = int(c_top[2] * (1 - t) + c_bot[2] * t)
            draw.line([(15, y), (min(w - 1, 200), y)], fill=(r, g, b))

        mask = Image.new("L", (w, h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rectangle([10, 10, min(w - 1, 205), min(h - 1, 125)], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(5))
        blurred = img.filter(ImageFilter.GaussianBlur(3))
        img.paste(blurred, mask=mask)

    # Format to target_w, target_h
    if style_id == 3:
        # Square crop/resize
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        cropped = img.crop((left, top, left + min_dim, top + min_dim))
        canvas = cropped.resize((1080, 1080), Image.Resampling.LANCZOS)
    else:
        # Fit into 1080x1350 with seamless background padding
        fit_h = 1310
        scale = fit_h / h
        fit_w = int(w * scale)
        scaled = img.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (target_w, target_h), (245, 248, 252))
        offset_x = (target_w - fit_w) // 2
        offset_y = (target_h - fit_h) // 2
        canvas.paste(scaled, (offset_x, offset_y))

        # Fill borders smoothly
        cdraw = ImageDraw.Draw(canvas)
        for y in range(target_h):
            sy = min(max(0, y - offset_y), fit_h - 1)
            left_col = scaled.getpixel((0, sy))
            right_col = scaled.getpixel((fit_w - 1, sy))
            cdraw.line([(0, y), (offset_x, y)], fill=left_col)
            cdraw.line([(offset_x + fit_w, y), (target_w, y)], fill=right_col)

        for x in range(target_w):
            top_col = canvas.getpixel((x, offset_y))
            bot_col = canvas.getpixel((x, offset_y + fit_h - 1))
            cdraw.line([(x, 0), (x, offset_y)], fill=top_col)
            cdraw.line([(x, offset_y + fit_h), (x, target_h - 1)], fill=bot_col)

    # Programmatically composite official Design Hub logo (100% transparent, built-in white outline)
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 155
        logo_h = int(logo.height * (logo_w / logo.width))
        logo_resized = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

        if style_id == 3:
            # Bottom center floor for Style 3
            lx = (target_w - logo_w) // 2
            ly = target_h - logo_h - 40
        else:
            # Top-left corner with 5.5% margin
            lx = 60
            ly = 55
        canvas.paste(logo_resized, (lx, ly), logo_resized)

    canvas.save(output_image_path, "JPEG", quality=95)
    return output_image_path


# =====================================================================
# PROMPT CRAFTER ACCORDING TO POSTER_DESIGN_SKILL.md
# =====================================================================

def craft_prompt_for_style(style_id: int, topic: str, price: str) -> str:
    """Builds a high-converting master prompt matching the chosen design archetype."""
    price_tag = price or "50 TK / 3 MONTHS"
    
    if style_id == 7:
        return (
            f"A premium modern SaaS promotional social media poster for {topic or 'Canva Pro subscription'}, "
            "inspired by clean tech UI and split bento grid design. Aspect ratio 3:4 vertical. "
            "Crisp light-mode aesthetic with soft off-white background and subtle ambient pastel glow in corners. "
            "Top Header: Modern bold brand title 'Canva Pro' in cyan-to-purple gradient with Bengali subheadline "
            "'স্মার্ট ডিজাইনের আল্টিমেট সলিউশন'. On the top right is a floating 3D sparkling colorful star icon. "
            "Top-left area is clean and reserved for logo overlay. "
            "Layout: Split bento grid. On the left: A large vibrant rounded hero card with deep Canva gradient "
            "(cyan #00C4CC transitioning to royal purple #7D2AE8). Inside the card is a 3D golden crown and Canva token, "
            "with bold prominent text 'UNLIMITED / Pro Features'. At the bottom of this hero card is a prominent, "
            f"unique stark-white floating ticket pill badge with soft drop shadow and bold vibrant purple Bengali text '[ মাত্র {price_tag} ]' "
            "that stands out uniquely from all other text on the poster. "
            "On the right: A vertical stack of 5 sleek, rounded white micro-cards with soft shadows. "
            "Each card features a colorful app icon (AI magic wand, scissors background remover, photo gallery, typography font, cloud storage) "
            "with English feature names and Bengali descriptions (Magic Studio AI, BG Remover, 100M+ Assets, Brand Kit, 1TB Cloud). "
            "Bottom: A horizontal rounded white trust card with 4 security icons (100% Safe, Instant Activation, Personal Gmail, Pay After Access), "
            "and below it a vibrant rounded Messenger button 'অর্ডার করতে মেসেজ করুন'. Ultra-clean vector graphics, 3D clay elements, hyper-realistic UI design."
        )
    elif style_id == 6:
        return (
            f"A premium promotional advertising poster for {topic or 'Canva Pro subscription'}. "
            "Aspect ratio 3:4 vertical. Dark cinematic futuristic studio background with glowing deep magenta-purple concentric circular aperture portals. "
            "Foreground: A handsome, smiling Bangladeshi young male creator in a stylish maroon overshirt over a white t-shirt, "
            "holding forward a modern black smartphone with thin bezels. The smartphone screen clearly shows the Canva Pro workspace. "
            "Orbiting around the phone are 4 photorealistic white 3D squircle app tiles with rounded beveled edges: "
            "1. Official Canva 3D logo with gradient, 2. Glowing AI magic wand for Magic Studio, 3. Golden crown for Pro Access, 4. Stock media gallery icon. "
            f"At the top center is a glowing neon magenta pill badge highlighting bold Bengali text '[ {price_tag} ]'. "
            "Top-left corner is clean and reserved for brand logo overlay. Photorealistic commercial advertising photography."
        )
    elif style_id == 2:
        return (
            f"A 1080x1350 portrait ultra-clean modern digital art poster for {topic or 'Canva Pro'}. "
            "Background: Deep obsidian navy with subtle smooth vignette and soft cyan and purple rim lighting. "
            "Top: Bold condensed headline 'CREATE WITHOUT LIMITS' in clean off-white lettering. Floating beside it is a tactile "
            "3D squircle tile of the official Canva logo (cyan to purple-violet gradient with white script) with realistic beveled depth and soft glow. "
            "Center: A stylish 3D character designer holding a glowing digital stylus, surrounded by floating 3D creative assets "
            "(glowing typography 'Aa', color swatch deck, neon sparkles). "
            f"Bottom: A sleek horizontal frosted-glass dock card with 1px glowing border containing bold amber text '{price_tag}', "
            "secondary trust line 'ACCESS FIRST | PAY LATER', and a rounded glowing CTA button 'GET ACCESS'. "
            "Top-left corner is completely clear and empty for direct brand logo overlay."
        )
    elif style_id == 1:
        return (
            f"A 1080x1350 portrait clean, bright, professional social media promo poster for {topic or 'Canva Pro'}. "
            "Background: Soft morning ivory-white studio gradient with gentle floor shadows. "
            "Left Side: Official 3D Canva squircle tile (cyan to purple gradient with white script) with title 'CANVA PRO'. "
            f"Dashed coupon box with highlighted amber price '[ {price_tag} ]'. 3 bullet points with colored icons detailing key benefits. "
            "Rounded solid CTA button 'GET ACCESS'. "
            "Right Side: Charming 3D character sitting casually on a glossy branded prop, smiling and pointing towards the offer on the left. "
            "Top-left corner is completely clear and empty for direct brand logo overlay."
        )
    elif style_id == 4:
        return (
            f"A 1080x1350 portrait museum-grade conceptual art poster celebrating creative empowerment for {topic or 'Canva Pro'}. "
            "Background: Matte deep prussian-blue wall with soft directional studio shadows and warm ambient glow. "
            "Bottom Surface: An ordinary wooden pencil lies beside a tactile physical 3D squircle token of the official Canva logo. "
            "Metaphor: From the sharp pencil tip, a single continuous drawn line sweeps upward in a graceful S-curve, gradually morphing "
            "into a fluid luminous ribbon of translucent frosted colored glass (glowing cyan and warm amber), ending at the top in an intricate "
            "glowing origami prism gently guided by an adult hand. "
            f"Below: Tall ivory condensed headline 'ANYONE CAN CREATE'. Centered amber pill badge with '[ {price_tag} ]'. "
            "Top-left corner is reserved clean for direct Design Hub brand logo placement."
        )
    elif style_id == 3:
        return (
            f"A square promotional poster for {topic or 'Canva Pro Pricing Plans'}. "
            "Cinematic dark studio floor with overhead dramatic spotlights. "
            "Center features 3 floating frosted-glass pricing cards side-by-side with 1px luminous borders. "
            f"Center hero card is elevated and glowing with a 3D Canva Pro badge, highlighting '{price_tag}'. "
            "Left and right cards display starter and extended packages. Ultra-premium glassmorphism, clean typography."
        )
    else:  # Style 5
        return (
            f"A patriotic vector art commemorative poster for {topic or 'Bangladesh Observance Day'}. "
            "Rich national colors, red and green geometric silhouettes of the National Monument (Jatiyo Smriti Soudho), "
            "birds in flight, clean Bengali typography, modern minimalist cultural vector aesthetic."
        )


# =====================================================================
# BOT COMMANDS & HANDLERS
# =====================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Studio Bot Welcome Menu."""
    if not check_auth(update):
        await update.message.reply_text("⛔ Unauthorized. This bot is dedicated to Design Hub administration.")
        return

    text = (
        "🎨 *Welcome to Design Hub Studio Bot!*\n\n"
        "This bot runs in the background on your Mac to generate studio-grade promotional posters "
        "and publish them directly to your Facebook Page.\n\n"
        "📌 *Quick Commands:*\n"
        "• `/designs` — Browse all 7 Design References sequentially with live photos\n"
        "• `/create` — Generate a new promotional poster (interactive picker)\n"
        "• `/create <style_num> <price>` — e.g. `/create 7 50tk`\n"
        "• `/help` — Full guide and prompt tips"
    )

    keyboard = [
        [
            InlineKeyboardButton("🖼️ Browse All 7 Styles (/designs)", callback_data="nav_design:0"),
        ],
        [
            InlineKeyboardButton("✨ Quick Create: Style 7 (50 TK)", callback_data="gen_quick:7:50tk"),
            InlineKeyboardButton("✨ Quick Create: Style 6 (99 TK)", callback_data="gen_quick:6:99tk"),
        ],
        [
            InlineKeyboardButton("🎨 Custom Create Menu", callback_data="menu_create"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_designs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /designs command: displays single carousel or sends all 7 sequentially."""
    if not check_auth(update):
        return

    args = context.args
    if args and args[0].lower() in ["all", "list"]:
        await send_all_designs(update.effective_chat.id, context)
        return

    # Default: Show Design 1 with interactive navigation
    await show_design_card(update.effective_chat.id, context, 0, is_new=True)


async def show_design_card(chat_id: int, context: ContextTypes.DEFAULT_TYPE, index: int, message_id: int = None, is_new: bool = False):
    """Renders one design card with previous/next buttons."""
    d = DESIGNS[index]
    total = len(DESIGNS)

    caption = (
        f"🎨 *[{index + 1}/{total}] {d['name']}*\n\n"
        f"✨ *DNA:* {d['dna']}\n"
        f"📐 *Layout Geometry:* {d['geometry']}\n"
        f"🎯 *Best For:* {d['triggers']}\n"
        f"📁 *Reference Folder:* `{d['folder']}`"
    )

    prev_idx = (index - 1) % total
    next_idx = (index + 1) % total

    keyboard = [
        [
            InlineKeyboardButton("◀️ Prev", callback_data=f"nav_design:{prev_idx}"),
            InlineKeyboardButton(f"📌 {index + 1} / {total}", callback_data="noop"),
            InlineKeyboardButton("Next ▶️", callback_data=f"nav_design:{next_idx}"),
        ],
        [
            InlineKeyboardButton(f"🎨 Generate in Style {d['id']}", callback_data=f"select_style:{d['id']}"),
        ],
        [
            InlineKeyboardButton("📚 Send All 7 to Chat", callback_data="send_all_designs"),
        ],
    ]

    img_path = WORKSPACE_DIR / d["image"]

    if is_new or not message_id:
        if img_path.exists():
            with open(img_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    else:
        # Edit existing photo message
        if img_path.exists():
            with open(img_path, "rb") as photo:
                media = InputMediaPhoto(media=photo, caption=caption, parse_mode="Markdown")
                await context.bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=media,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )


async def send_all_designs(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Sends all 7 design references sequentially into the chat."""
    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="📤 *Sending all 7 design reference archetypes sequentially...*",
        parse_mode="Markdown",
    )

    for i, d in enumerate(DESIGNS):
        img_path = WORKSPACE_DIR / d["image"]
        caption = (
            f"🎨 *Design #{d['id']}: {d['name']}*\n"
            f"──────────────────────\n"
            f"✨ *Visual DNA:* {d['dna']}\n"
            f"📐 *Geometry:* {d['geometry']}\n"
            f"🎯 *Context:* {d['triggers']}\n"
            f"📂 *Archive:* `{d['folder']}`"
        )
        keyboard = [
            [InlineKeyboardButton(f"🎨 Create Poster in Style {d['id']}", callback_data=f"select_style:{d['id']}")]
        ]

        if img_path.exists():
            with open(img_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
        await asyncio.sleep(0.5)

    await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)


# =====================================================================
# GENERATION ENGINE
# =====================================================================

async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /create command."""
    if not check_auth(update):
        return

    args = context.args
    if not args:
        # Show interactive style picker
        keyboard = []
        for d in DESIGNS:
            keyboard.append([InlineKeyboardButton(f"Style {d['id']}: {d['headline']}", callback_data=f"select_style:{d['id']}")])
        await update.message.reply_text(
            "🎨 *Choose a Design Style to Generate:*\n\n"
            "Pick one of the 7 archetypes from your design archive:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # Parse arguments: e.g. /create 7 50tk or /create 6 canva 99tk
    style_num = 7
    price = "50 TK / 3 MONTHS"
    topic = "Canva Pro Subscription"

    try:
        style_num = int(args[0])
        if len(args) > 1:
            price = " ".join(args[1:])
    except ValueError:
        topic = " ".join(args)

    await execute_generation(update.effective_chat.id, context, style_num, topic, price)


async def execute_generation(chat_id: int, context: ContextTypes.DEFAULT_TYPE, style_id: int, topic: str, price: str):
    """Executes the AI generation and post-processing pipeline."""
    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⏳ *Preparing Style {style_id} Poster Generation...*\n"
             f"• Package: `{price}`\n"
             f"• Model: `Google Imagen 3 (imagen-3.0-generate-002)`\n"
             f"• Layout: 4:5 Facebook Portrait (1080x1350)",
        parse_mode="Markdown",
    )

    prompt = craft_prompt_for_style(style_id, topic, price)
    logger.info(f"Crafted prompt for Style {style_id}: {prompt[:150]}...")

    # Attempt generation via Gemini Image API
    if not GEMINI_API_KEY:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text="❌ `GEMINI_API_KEY` is not set in `.env`.",
            parse_mode="Markdown",
        )
        return

    # Call Google API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]}
    }

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text="🎨 *Contacting Google Image Engine...*\nGenerating high-resolution artwork...",
            parse_mode="Markdown",
        )

        res = requests.post(url, json=payload, timeout=60)

        if res.status_code == 200:
            data = res.json()
            # Extract image bytes
            candidate = data.get("candidates", [{}])[0]
            parts = candidate.get("content", {}).get("parts", [])
            img_b64 = None
            for p in parts:
                if "inlineData" in p:
                    img_b64 = p["inlineData"].get("data")
                    break

            if img_b64:
                raw_bytes = base64.b64decode(img_b64)
                timestamp = int(time.time())
                raw_path = GENERATED_DIR / f"raw_style_{style_id}_{timestamp}.jpg"
                final_path = GENERATED_DIR / f"poster_style_{style_id}_{timestamp}.jpg"

                with open(raw_path, "wb") as f:
                    f.write(raw_bytes)

                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text="📐 *Artwork received!*\nApplying 1080x1350 formatting & compositing Design Hub brand logo...",
                    parse_mode="Markdown",
                )

                post_process_poster(raw_path, final_path, style_id)

                # Send finished poster
                caption = (
                    f"🎉 *Poster Generated Successfully!*\n"
                    f"• *Style Archetype:* Style {style_id}\n"
                    f"• *Dimensions:* 1080×1350 (4:5 Facebook Portrait)\n"
                    f"• *Price Tag:* `{price}`\n"
                    f"• *Logo Overlay:* Official Design Hub Logo (Top-Left)\n"
                    f"• *File:* `{final_path.name}`"
                )

                keyboard = [
                    [
                        InlineKeyboardButton("🚀 Publish to Facebook Page", callback_data=f"publish_fb:{final_path.name}"),
                    ],
                    [
                        InlineKeyboardButton("🔄 Re-generate", callback_data=f"gen_quick:{style_id}:{price}"),
                        InlineKeyboardButton("🖼️ View Other Styles", callback_data="nav_design:0"),
                    ]
                ]

                with open(final_path, "rb") as photo:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )

                await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
                return
            else:
                raise Exception("No image data found in Google API response.")

        elif res.status_code == 429:
            # Quota notice with clear instructions
            error_data = res.json()
            error_msg = error_data.get("error", {}).get("message", "Quota exceeded.")
            
            help_text = (
                "⚠️ *Google AI Studio Quota Notice (429)*\n\n"
                "Google requires a linked Pay-as-you-go billing account to generate images via the API.\n\n"
                "🔗 *How to Unlock:*\n"
                "1. Go to [aistudio.google.com](https://aistudio.google.com/app/plan_information)\n"
                "2. Click **Set up billing** on your Gemini API key project.\n"
                "*(Costs only ~$0.03 / 3.5 BDT per image)*\n\n"
                "📋 *Master Prompt Crafted by Bot:*\n"
                f"```\n{prompt}\n```"
            )
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=help_text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
            return
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"❌ *Google API Error ({res.status_code}):*\n`{res.text[:300]}`",
                parse_mode="Markdown",
            )
            return

    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ *Generation Failed:* {str(e)}",
            parse_mode="Markdown",
        )


# =====================================================================
# CALLBACK QUERY HANDLER
# =====================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline keyboard interactions."""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    if data.startswith("nav_design:"):
        idx = int(data.split(":")[1])
        await show_design_card(chat_id, context, idx, message_id=message_id, is_new=False)

    elif data == "send_all_designs":
        await send_all_designs(chat_id, context)

    elif data.startswith("select_style:"):
        style_id = int(data.split(":")[1])
        keyboard = [
            [
                InlineKeyboardButton("🏷️ 25 TK Package", callback_data=f"gen_quick:{style_id}:25tk"),
                InlineKeyboardButton("🏷️ 50 TK Package", callback_data=f"gen_quick:{style_id}:50tk"),
            ],
            [
                InlineKeyboardButton("🏷️ 99 TK Package", callback_data=f"gen_quick:{style_id}:99tk"),
                InlineKeyboardButton("🏷️ 150 TK (1 Year)", callback_data=f"gen_quick:{style_id}:150tk"),
            ],
            [
                InlineKeyboardButton("⬅️ Back to Designs", callback_data=f"nav_design:{style_id - 1}"),
            ]
        ]
        await query.message.reply_text(
            f"🎯 *Style {style_id} Selected!*\nPick a pricing package to generate:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("gen_quick:"):
        _, style_id_str, price = data.split(":")
        style_id = int(style_id_str)
        await execute_generation(chat_id, context, style_id, "Canva Pro Subscription", price)

    elif data.startswith("publish_fb:"):
        filename = data.split(":")[1]
        target_file = GENERATED_DIR / filename
        if not target_file.exists():
            await query.message.reply_text("❌ Poster file not found on disk.")
            return

        await query.message.reply_text("⏳ Generating AI caption and publishing to Facebook Page...")
        
        # Call publish_poster.py logic
        try:
            from publish_poster import publish_poster, generate_caption_for_poster
            caption = generate_caption_for_poster(str(target_file), "Official Canva Pro promo from Studio Bot")
            success = publish_poster(str(target_file), caption)
            if success:
                await query.message.reply_text(
                    f"✅ *Successfully Published to Facebook Page!*\n\n"
                    f"📝 *Caption Used:*\n{caption}",
                    parse_mode="Markdown",
                )
            else:
                await query.message.reply_text("❌ Facebook publishing failed. Check FB_PAGE_ACCESS_TOKEN.")
        except Exception as e:
            await query.message.reply_text(f"❌ Error publishing to Facebook: {e}")


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================

async def post_init(application):
    """Sets bot menu commands."""
    commands = [
        BotCommand("designs", "Browse all 7 design reference archetypes"),
        BotCommand("create", "Generate a new promotional poster"),
        BotCommand("start", "Open Studio dashboard"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Studio Bot commands registered successfully.")


def main():
    if not STUDIO_BOT_TOKEN:
        print("❌ Error: STUDIO_BOT_TOKEN not set.")
        sys.exit(1)

    print(f"🚀 Starting Design Hub Studio Bot (@designposterbot)...")
    app = ApplicationBuilder().token(STUDIO_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("designs", cmd_designs))
    app.add_handler(CommandHandler("create", cmd_create))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()


if __name__ == "__main__":
    main()
