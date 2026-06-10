# ⭐ Bintang Auto Bot

Auto claim ads & tasks untuk **@EarnStarsAppBot** (Telegram Mini App).

## 🚀 Quick Start (Termux)

```bash
pkg install python git -y && pip install telethon requests && \
git clone https://github.com/sagita128/bintang-auto-bot && \
cd bintang-auto-bot && python3 bot.py
```

## 📋 Yang Dibutuhkan

1. **API ID & API Hash** — dari https://my.telegram.org
2. **Nomor HP Telegram** — format +62xxx
3. **Kode verifikasi** — dikirim ke Telegram lo

## 🎮 Commands

```bash
python3 bot.py              # Jalankan sekali
python3 bot.py --loop       # Auto 24/7
python3 bot.py --status     # Cek balance
python3 bot.py --setup      # Setup ulang
```

## 🏃 Background 24/7

```bash
nohup python3 bot.py --loop &
```

## ✅ Fitur

- 🎬 Auto claim ads (+0.2⭐ per jam)
- 📋 Auto claim tasks (subscribe, open link, dll)
- 🔄 Auto refresh auth
- ⏰ Cooldown aware
- 💾 State persistence (gak repeat task)
- 📝 Logging ke file
