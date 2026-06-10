#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  SETUP BINTANG BOT DI TERMUX (Telegram User API Version)
# ═══════════════════════════════════════════════════════════════
#
#  Cara pakai:
#  1. Install Termux dari F-Droid
#  2. Jalankan: bash setup_termux.sh
#  3. Edit config.json dengan api_id, api_hash, nomor HP
#  4. Jalankan: python3 bintang_auto.py
#
# ═══════════════════════════════════════════════════════════════

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       ⭐ BINTANG BOT TERMUX SETUP ⭐                         ║"
echo "║       Telegram User API Version                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Update packages
echo "[1/4] Updating packages..."
pkg update -y 2>/dev/null || apt update -y

# Install Python
echo "[2/4] Installing Python..."
pkg install -y python 2>/dev/null || apt install -y python3

# Install pip + dependencies
echo "[3/4] Installing dependencies..."
pip install telethon 2>/dev/null || pip3 install telethon

# Setup
echo "[4/4] Setting up..."
cd ~
mkdir -p bintang-bot
cd bintang-bot

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Setup selesai!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  📋 Langkah selanjutnya:"
echo ""
echo "  1. Dapatkan API credentials:"
echo "     → Buka https://my.telegram.org"
echo "     → Login → API Development Tools"
echo "     → Buat aplikasi baru"
echo "     → Catat api_id dan api_hash"
echo ""
echo "  2. Edit config.json:"
echo "     nano config.json"
echo "     Isi: api_id, api_hash, phone"
echo ""
echo "  3. Jalankan bot:"
echo "     python3 bintang_auto.py"
echo ""
echo "  4. Login pertama kali:"
echo "     → Masukkan kode verifikasi dari Telegram"
echo ""
echo "  5. Biarkan jalan di background:"
echo "     → Ctrl+C untuk stop"
echo "     → nohup python3 bintang_auto.py &"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
