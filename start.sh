#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ⭐ BINTANG BOT - Quick Start untuk Akun Baru ⭐
# ═══════════════════════════════════════════════════════════════
#
#  Cara pakai (1 command di Termux):
#
#  pkg install python git -y && pip install telethon requests && \
#  git clone https://github.com/rusmanaid/bintang bintang-bot && \
#  cd bintang-bot && python3 bot.py
#
#  Atau kalau udah clone:
#  cd bintang-bot && python3 bot.py
#
# ═══════════════════════════════════════════════════════════════

echo "⭐ Bintang Bot - Quick Start"
echo ""

# Cek Python
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    pkg update -y && pkg install -y python
fi

# Cek dependencies
echo "Checking dependencies..."
pip install telethon requests 2>/dev/null

# Cek config
if [ ! -f "config.json" ]; then
    echo ""
    echo "📋 SETUP BARU!"
    echo "Bot akan minta API credentials dan nomor HP."
    echo "Dapatkan API dari: https://my.telegram.org"
    echo ""
fi

# Jalankan bot
python3 bot.py "$@"
