#!/bin/bash
# Double-click this launcher to start the Design Hub Work & Task Scheduler Bot
cd "$(dirname "$0")"
echo "======================================================="
echo "   ⏰ DESIGN HUB - WORK & TASK SCHEDULER (BOT-2)      "
echo "   Telegram Bot: @designposterbot                     "
echo "======================================================="
echo ""
echo "Starting Work & Task Scheduler daemon..."
if [ -f "./.venv/bin/python" ]; then
    ./.venv/bin/python studio_bot.py
else
    python3 studio_bot.py
fi
