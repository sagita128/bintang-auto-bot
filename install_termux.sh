#!/bin/bash
echo "⭐ Installing Bintang Bot..."
mkdir -p ~/bintang-bot && cd ~/bintang-bot
pip install telethon requests 2>/dev/null
echo "✅ Dependencies installed!"
echo "Run: python3 bot.py"
