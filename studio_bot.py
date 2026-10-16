#!/usr/bin/env python3
"""
Design Hub - Dedicated Studio Poster Generator Bot
Telegram Bot: @designposterbot
Runs natively on macOS in the background to:
1. Browse and showcase all 7 Design Reference Archetypes at once (/designs)
2. Generate promotional posters using Google Imagen 3 / Gemini Image models (with Cloud FLUX fallback)
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
import urllib.parse
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

# All 7 Design Archetypes in folder sequence with master posters
DESIGNS = [
    {
        "id": 1,
        "name": "Design 1",
        "title": "Style 1: Clean & Bright Studio Character",
        "image": "designs/design-1_reference/canva_pro_studio_promo_1080x1350.jpg",
    },
    {
        "id": 2,
        "name": "Design 2",
        "title": "Style 2: Atmospheric Dark Mode & Floating 3D Elements",
        "image": "designs/design-2_reference/dynamic_horizontal_promo_1080x1350.jpg",
    },
    {
        "id": 3,
        "name": "Design 3",
        "title": "Style 3: Ultra-Premium Glassmorphism Pricing Tiles",
        "image": "designs/design-3_reference/reference.jpg",
    },
    {
        "id": 4,
        "name": "Design 4",
        "title": "Style 4: Poetic Conceptual Art & Physical Metaphor",
        "image": "designs/design-4_reference/canva_conceptual_promo_1080x1350.jpg",
    },
    {
        "id": 5,
        "name": "Design 5",
        "title": "Style 5: National & Observance Day Vector Art",
        "image": "designs/design-5_reference/national_revolution_and_solidarity_day_celebration.jpg",
    },
    {
        "id": 6,
        "name": "Design 6",
        "title": "Style 6: Real Model & Floating 3D Feature Badges",
        "image": "designs/design-6_reference/canva_pro_mobile_promo_1080x1350.jpg",
    },
    {
        "id": 7,
        "name": "Design 7",
        "title": "Style 7: Premium SaaS Split-Bento & Feature Stack Grid",
        "image": "designs/design-7_reference/canva_pro_bento_promo_1080x1350.jpg",
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
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        cropped = img.crop((left, top, left + min_dim, top + min_dim))
        canvas = cropped.resize((1080, 1080), Image.Resampling.LANCZOS)
    else:
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
            lx = (target_w - logo_w) // 2
            ly = target_h - logo_h - 40
        else:
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
            f"A clean, bright, professional social media promotional poster for {topic or 'Canva Pro subscription'}, "
            "inspired by Pixar 3D studio art. Aspect ratio 3:4 vertical. "
            "Background: Warm morning ivory-white daylight studio gradient with soft diffused floor contact shadows. "
            "Layout: Split screen. Left side: Official 3D Canva squircle tile with bold modern title 'CANVA PRO'. "
            f"Dashed coupon box with a prominent, unique golden amber pill badge displaying '[ মাত্র {price_tag} ]' with subtle shadow. "
            "3 bullet points with vibrant colored icons: 'Magic Studio AI', '1-Click Background Remover', '100M+ Premium Assets'. "
            "Below is a solid rounded CTA button 'GET ACCESS NOW' and trust line 'Access First | Pay Later'. "
            "Right side: A charming, friendly 3D Pixar-style young student creator with warm smile, wearing a casual denim jacket, "
            "sitting relaxed on a glossy white pedestal, holding a digital tablet and gesturing enthusiastically toward the offer on the left. "
            "Top-left corner is completely clear and empty for brand logo overlay."
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
        "🎨 *Design Hub Studio Bot*\n\n"
        "• `/designs` — Show all 7 design references at once\n"
        "• `/create <style_num> <price>` — e.g. `/create 7 50tk`\n"
        "• `/create` — Open interactive picker"
    )

    keyboard = [
        [
            InlineKeyboardButton("🖼️ Show All 7 Designs", callback_data="send_all_designs"),
        ],
        [
            InlineKeyboardButton("✨ Create Style 7 (50 TK)", callback_data="gen_quick:7:50tk"),
            InlineKeyboardButton("✨ Create Style 1 (25 TK)", callback_data="gen_quick:1:25tk"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_designs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /designs command: immediately sends all 7 designs with minimalist captions."""
    if not check_auth(update):
        return
    await send_all_designs(update.effective_chat.id, context)


async def send_all_designs(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Sends all 7 design references with clean, minimalist caption: simply Design Number."""
    total = len(DESIGNS)
    for i, d in enumerate(DESIGNS):
        img_path = WORKSPACE_DIR / d["image"]
        caption = f"🎨 *Design {d['id']}*"

        keyboard = [
            [
                InlineKeyboardButton(f"🎨 Create in Style {d['id']}", callback_data=f"select_style:{d['id']}"),
            ]
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
        await asyncio.sleep(0.3)


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles natural language messages like 'show designs' or 'designs'."""
    if not check_auth(update):
        return

    text = update.message.text.lower().strip()
    if any(k in text for k in ["show design", "show all design", "all design", "designs", "design"]):
        await send_all_designs(update.effective_chat.id, context)
    elif text.startswith("create ") or text.startswith("/create"):
        parts = update.message.text.split()[1:]
        context.args = parts
        await cmd_create(update, context)
    else:
        await cmd_start(update, context)


# =====================================================================
# GENERATION ENGINE (WITH SEAMLESS CLOUD FLUX FALLBACK)
# =====================================================================

async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /create command."""
    if not check_auth(update):
        return

    args = context.args
    if not args:
        keyboard = []
        for d in DESIGNS:
            keyboard.append([InlineKeyboardButton(f"Design {d['id']}: {d['title']}", callback_data=f"select_style:{d['id']}")])
        await update.message.reply_text(
            "🎨 *Choose a Design Style:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

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
    """Executes AI generation (Google Imagen 3 with automatic Cloud FLUX fallback) and post-processing."""
    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⏳ *Generating Style {style_id} Poster...*\n"
             f"• Package: `{price}`\n"
             f"• Ratio: 4:5 Facebook Portrait (1080x1350)",
        parse_mode="Markdown",
    )

    prompt = craft_prompt_for_style(style_id, topic, price)
    timestamp = int(time.time())
    raw_path = GENERATED_DIR / f"raw_style_{style_id}_{timestamp}.jpg"
    final_path = GENERATED_DIR / f"poster_style_{style_id}_{timestamp}.jpg"

    raw_bytes = None
    engine_name = "Google Imagen 3"

    # Step 1: Attempt Google Gemini Image API
    if GEMINI_API_KEY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]}
        }
        try:
            res = requests.post(url, json=payload, timeout=40)
            if res.status_code == 200:
                data = res.json()
                candidate = data.get("candidates", [{}])[0]
                parts = candidate.get("content", {}).get("parts", [])
                for p in parts:
                    if "inlineData" in p:
                        raw_bytes = base64.b64decode(p["inlineData"]["data"])
                        break
            elif res.status_code == 429:
                logger.info("Google API returned 429 quota. Falling back to Cloud FLUX engine seamlessly...")
        except Exception as e:
            logger.warning(f"Google API request failed: {e}. Switching to Cloud FLUX engine...")

    # Step 2: Seamless Cloud Fallback (FLUX Cloud - Free, Unlimited, High Quality)
    if not raw_bytes:
        try:
            engine_name = "Cloud FLUX"
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text="🎨 *Generating artwork via Cloud FLUX engine...*",
                parse_mode="Markdown",
            )
            encoded_prompt = urllib.parse.quote(prompt)
            # 768x1024 or 864x1152 matches ~3:4 / 4:5
            flux_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=864&height=1152&nologo=true&model=flux"
            flux_res = requests.get(flux_url, timeout=45)
            if flux_res.status_code == 200 and len(flux_res.content) > 2000:
                raw_bytes = flux_res.content
        except Exception as e:
            logger.error(f"Fallback engine failed: {e}")

    if not raw_bytes:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text="❌ Image generation timed out. Please try again.",
            parse_mode="Markdown",
        )
        return

    # Step 3: Mac Post-Processing Pipeline
    try:
        with open(raw_path, "wb") as f:
            f.write(raw_bytes)

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text="📐 *Formatting to 1080x1350 & compositing Design Hub brand logo...*",
            parse_mode="Markdown",
        )

        post_process_poster(raw_path, final_path, style_id)

        caption = (
            f"🎉 *Design {style_id} Poster Ready!*\n"
            f"• *Price:* `{price}`\n"
            f"• *Dimensions:* 1080×1350 (4:5 Facebook Portrait)\n"
            f"• *Engine:* `{engine_name}`"
        )

        keyboard = [
            [
                InlineKeyboardButton("🚀 Publish to Facebook Page", callback_data=f"publish_fb:{final_path.name}"),
            ],
            [
                InlineKeyboardButton("🔄 Re-generate", callback_data=f"gen_quick:{style_id}:{price}"),
                InlineKeyboardButton("🖼️ All Designs", callback_data="send_all_designs"),
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

    except Exception as e:
        logger.error(f"Post processing error: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ Error processing poster: {e}",
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

    if data == "send_all_designs":
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
                InlineKeyboardButton("🖼️ Back to All Designs", callback_data="send_all_designs"),
            ]
        ]
        await query.message.reply_text(
            f"🎯 *Design {style_id} Selected!*\nPick a pricing package to generate:",
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
        BotCommand("designs", "Show all 7 designs"),
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    app.run_polling()


if __name__ == "__main__":
    main()
