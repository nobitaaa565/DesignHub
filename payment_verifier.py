#!/usr/bin/env python3
"""
Payment Proof Verifier for Design Hub
Uses Google Gemini 3.8 Flash Vision to extract TrxID, Amount, and Provider
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
    Analyzes a bKash/Nagad/Rocket screenshot using Gemini 3.8 Flash Vision.
    Returns: dict with provider, trx_id, amount, sender, status, raw_summary
    """
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY is not configured."}

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = (
        "You are an expert financial proof auditor in Bangladesh for bKash, Nagad, Rocket, and Upay.\n"
        "Carefully examine this screenshot and extract the payment confirmation details.\n"
        "Return ONLY a clean JSON object with this exact format:\n"
        "{\n"
        '  "is_payment_proof": true,\n'
        '  "provider": "bKash" | "Nagad" | "Rocket" | "Upay" | "Bank" | "Unknown",\n'
        '  "trx_id": "Extracted Transaction ID or null",\n'
        '  "amount": "Extracted amount (e.g. 25.00 Tk, 50.00 Tk) or null",\n'
        '  "sender": "Sender phone number or null",\n'
        '  "recipient": "Recipient/Merchant number or null",\n'
        '  "status": "Successful" | "Pending" | "Failed" | "Unknown",\n'
        '  "timestamp": "Date and time on receipt or null"\n'
        "}\n"
        "If this image is NOT a payment receipt/screenshot, set is_payment_proof: false."
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

    try:
        res = requests.post(url, json=payload, timeout=25)
        if res.status_code == 200:
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Clean markdown code blocks if any
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
            clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE).strip()
            
            try:
                parsed = json.loads(clean_text)
                return parsed
            except Exception:
                # Fallback regex extraction
                trx_match = re.search(r"TrxID\s*[:\"'\s]?\s*([A-Za-z0-9]{8,12})", raw_text, re.I)
                amount_match = re.search(r"(\d+(?:\.\d{1,2})?\s*(?:Tk|৳|TK))", raw_text, re.I)
                return {
                    "is_payment_proof": bool(trx_match),
                    "provider": "bKash" if "bKash" in raw_text else ("Nagad" if "Nagad" in raw_text else "Unknown"),
                    "trx_id": trx_match.group(1) if trx_match else None,
                    "amount": amount_match.group(1) if amount_match else None,
                    "status": "Successful",
                    "raw_text": raw_text[:200]
                }
        else:
            logger.error(f"Gemini API error ({res.status_code}): {res.text}")
            return {"error": f"API Error: {res.status_code}"}
    except Exception as e:
        logger.error(f"Error analyzing screenshot: {e}")
        return {"error": str(e)}


def extract_trx_from_text(text: str) -> dict:
    """Extracts TrxID from SMS or plain text using regex."""
    # bKash / Nagad pattern: 8 to 12 alphanumeric characters
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
    test_sms = "You have received Tk 50.00 from 01712345678. Fee Tk 0.00. Balance Tk 1,250.00. TrxID 9K8X2LM7 on 15/10/2026."
    print("Test text extraction:", extract_trx_from_text(test_sms))
