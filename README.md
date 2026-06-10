# ⭐ Bintang Auto Bot

Auto claim ads & tasks untuk **@EarnStarsAppBot** di Telegram.

## 🚀 Quick Start (Termux)

```bash
# Install Termux dari F-Droid, lalu jalankan:

pkg install python git -y && pip install telethon requests && \
git clone https://github.com/rusmanaid/bintang bintang-bot && \
cd bintang-bot && python3 bot.py
```

## 📋 Setup

Bot akan minta:
1. **API ID** (angka) — dari https://my.telegram.org
2. **API Hash** (teks) — dari https://my.telegram.org
3. **Nomor HP** — format +62xxx
4. **Kode verifikasi** — dikirim ke Telegram

Sekali setup aja, terus otomatis!

## 🎮 Commands

```bash
python3 bot.py              # Jalankan sekali
python3 bot.py --loop       # Auto terus (24/7)
python3 bot.py --status     # Cek balance
python3 bot.py --setup      # Setup ulang
```

## 🏃 Background (24/7)

```bash
# 1. Pasang wakelock (biar HP gak matiin Termux)
termux-wake-lock

# 2. Buat screen session
screen -S bintang

# 3. Jalankan bot
python3 bot.py --loop

# 4. Detach (keluar tanpa matiin bot)
# Tekan: Ctrl+A, lalu D

# 5. Tutup Termux aja! Bot tetap jalan
```

Mau balik ke bot:
```bash
screen -r bintang
```

Cara ini bikin:
- ✅ Bot jalan terus walau Termux ditutup
- ✅ Hemat baterai (gak perlu buka Termux)
- ✅ Auto-reconnect kalau koneksi putus

## ✅ Fitur

- 🎬 Auto claim ads (+0.2⭐ per jam)
- 📋 Auto claim tasks (subscribe, open link, dll)
- 🔄 Auto refresh auth dari Telegram
- ⏰ Cooldown aware (1 jam antar ad)
- 💾 State persistence (gak repeat task)
- 📝 Logging ke file

## 📊 Monitor

```bash
# Lihat log
tail -f bot.log

# Cek status
python3 bot.py --status
```

## 🛑 Stop Bot

```bash
# Kalau jalan di screen
screen -r bintang
# Tekan Ctrl+C untuk stop

# Kalau jalan di nohup
pkill -f bot.py

# Matiin screen session juga
screen -X -S bintang quit
```

## ⚠️ Notes

- Auth expire setelah beberapa jam, bot auto-refresh
- Ads cooldown 1 jam (bukan 2 jam seperti dugaan awal)
- Tasks yang udah di-claim gak akan di-claim lagi
- Bot butuh koneksi internet stabil
