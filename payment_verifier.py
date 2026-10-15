#!/usr/bin/env python3
"""
Payment Proof Verifier for Design Hub
Uses Google Gemini Vision (multi-model fallback) to extract TrxID, Amount, and Provider
from bKash, Nagad, and Rocket payment screenshots.
"""

import os
import re
import json
import base64
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
logger = logging.getLogger("PaymentVerifier")


def analyze_payment_screenshot(image_bytes: bytes) -> dict:
    """
    Analyzes a bKash/Nagad/Rocket screenshot with multi-model fallback.
    Returns: dict with is_payment_proof, provider, trx_id, amount, recipient, timestamp
    """
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY is not configured."}

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = (
        "Examine this payment confirmation receipt or screenshot from Bangladesh Mobile Banking.\n"
        "Extract the transaction details into valid JSON with this exact format:\n"
        "{\n"
        '  "is_payment_proof": true,\n'
        '  "provider": "bKash" | "Nagad" | "Rocket" | "Upay" | "Bank",\n'
        '  "trx_id": "Exact Transaction ID (TrxID)",\n'
        '  "amount": "Exact amount (e.g. 50.00 Tk, ৳50.00)",\n'
        '  "sender": "Sender phone number if visible, else null",\n'
        '  "recipient": "Recipient/Merchant number or name if visible, else null",\n'
        '  "timestamp": "Date and time if visible, else null"\n'
        "}\n"
        "If this image has NO payment/transaction details at all, return {\"is_payment_proof\": false}.\n"
        "Output ONLY raw JSON."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_image
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 600
        }
    }

    models_to_try = ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-flash-latest"]
    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE).strip()
                try:
                    parsed = json.loads(clean_text)
                    if parsed.get("trx_id") and not parsed.get("is_payment_proof"):
                        parsed["is_payment_proof"] = True
                    return parsed
                except Exception:
                    trx_match = re.search(r"TrxID\s*[:\"'\s]?\s*([A-Za-z0-9]{8,12})", raw_text, re.I)
                    amount_match = re.search(r"(\d+(?:\.\d{1,2})?\s*(?:Tk|৳|TK))", raw_text, re.I)
                    return {
                        "is_payment_proof": bool(trx_match),
                        "provider": "bKash" if "bKash" in raw_text else ("Nagad" if "Nagad" in raw_text else "Unknown"),
                        "trx_id": trx_match.group(1) if trx_match else None,
                        "amount": amount_match.group(1) if amount_match else None,
                        "status": "Successful"
                    }
            elif res.status_code in (503, 429, 404):
                logger.warning(f"Model {m} returned {res.status_code}, trying next model...")
                continue
        except Exception as e:
            logger.warning(f"Error on {m}: {e}, trying next model...")
            continue

    return {"error": "Vision service temporarily busy. Please try again."}


def extract_trx_from_text(text: str) -> dict:
    """Extracts TrxID from SMS or plain text using regex."""
    trx_match = re.search(r"(?:TrxID|TxnID|Transaction ID|আইডি)\s*[:#\s]?\s*([A-Za-z0-9]{8,12})", text, re.I)
    amount_match = re.search(r"(?:Tk|৳|BDT)\.?\s*(\d+(?:\.\d{1,2})?)|(\d+(?:\.\d{1,2})?)\s*(?:Tk|৳|BDT)", text, re.I)
    
    amount_val = None
    if amount_match:
        amount_val = amount_match.group(1) or amount_match.group(2)
        amount_val = f"{amount_val} TK"

    provider = "Unknown"
    if re.search(r"bkash|বিকাশ", text, re.I):
        provider = "bKash"
    elif re.search(r"nagad|নগদ", text, re.I):
        provider = "Nagad"
    elif re.search(r"rocket|রকেট", text, re.I):
        provider = "Rocket"

    return {
        "found": bool(trx_match),
        "provider": provider,
        "trx_id": trx_match.group(1).upper() if trx_match else None,
        "amount": amount_val
    }


if __name__ == "__main__":
    with open("sample_bkash_payment.png", "rb") as f:
        res = analyze_payment_screenshot(f.read())
    print("Test Result:")
    print(json.dumps(res, indent=2))
