#!/bin/bash
# Double-click this launcher to start the Design Hub Studio Poster Bot
cd "$(dirname "$0")"
echo "======================================================="
echo "   🚀 DESIGN HUB - STUDIO POSTER GENERATOR BOT        "
echo "   Telegram Bot: @designposterbot                     "
echo "======================================================="
echo ""
echo "Starting bot in local studio environment..."
./.venv/bin/python studio_bot.py
