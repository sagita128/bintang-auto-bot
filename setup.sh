#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ⭐ BINTANG BOT - Termux Setup Script ⭐
# ═══════════════════════════════════════════════════════════════
#
#  Cara pakai:
#  1. Install Termux dari F-Droid (bukan Play Store!)
#  2. Buka Termux, jalankan:
#     pkg install git -y && git clone https://github.com/rusmanaid/bintang bintang-bot && cd bintang-bot && bash setup.sh
#  3. Atau manual:
#     bash setup.sh
#  4. Jalankan: python3 bot.py
#
# ═══════════════════════════════════════════════════════════════

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       ⭐ BINTANG BOT - Termux Setup ⭐                       ║"
echo "║       Auto claim @EarnStarsAppBot                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Update
echo "[1/3] Updating packages..."
pkg update -y 2>/dev/null
pkg install -y python 2>/dev/null

# Install dependencies
echo "[2/3] Installing Python dependencies..."
pip install telethon requests 2>/dev/null

# Done
echo "[3/3] Setup selesai!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Semua terinstall!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  🚀 Jalankan bot:"
echo ""
echo "     python3 bot.py"
echo ""
echo "  📋 Bot akan minta:"
echo "     1. API ID & API Hash (dari https://my.telegram.org)"
echo "     2. Nomor HP Telegram"
echo "     3. Kode verifikasi"
echo ""
echo "  🔄 Setelah setup, bot jalan otomatis:"
echo ""
echo "     python3 bot.py --loop       ← auto terus"
echo "     python3 bot.py --status     ← cek balance"
echo ""
echo "  🏃 Background:"
echo "     nohup python3 bot.py --loop &"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
