#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║       ⭐ BINTANG AUTO BOT v2 - Termux Version ⭐              ║
║  Auto claim ads & tasks untuk @EarnStarsAppBot               ║
║  Jalankan di Termux, sekali setup terus otomatis 24/7        ║
╚══════════════════════════════════════════════════════════════╝

Cara pakai:
1. Install Termux dari F-Droid
2. bash setup.sh
3. python3 bot.py
4. Login sekali (nomor HP + kode verifikasi)
5. Bot jalan otomatis 24/7
"""

import asyncio
import json
import sys
import os
import time
import requests as req
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

try:
    from telethon import TelegramClient
    from telethon.tl import functions, types
    from telethon.errors import FloodWaitError
except ImportError:
    print("[!] Install telethon: pip install telethon")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
STATE_FILE = BASE_DIR / "state.json"
SESSION_FILE = BASE_DIR / "session"
LOG_FILE = BASE_DIR / "bot.log"

API_BASE = "https://spinhub.cc"
DEFAULT_BOT = "EarnStarsAppBot"

# ═══════════════════════════════════════════════════════════════
#  LOGGING (simple, Termux-friendly)
# ═══════════════════════════════════════════════════════════════

def log(level, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

def info(msg): log("INFO", msg)
def error(msg): log("ERROR", msg)
def warn(msg): log("WARN", msg)
def success(msg): log("✓", msg)

# ═══════════════════════════════════════════════════════════════
#  CONFIG & STATE
# ═══════════════════════════════════════════════════════════════

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        "balance_start": 0,
        "ads_claimed": 0,
        "tasks_claimed": 0,
        "total_earned": 0.0,
        "last_run": None,
        "last_ad_claim": None,
        "claimed_ids": [],
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)

# ═══════════════════════════════════════════════════════════════
#  SETUP WIZARD (untuk akun baru)
# ═══════════════════════════════════════════════════════════════

async def setup_wizard():
    """Setup interaktif untuk akun baru"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║       ⭐ SETUP WIZARD - Akun Baru ⭐                          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Dapatkan API credentials
    print("📋 Langkah 1: Dapatkan API credentials")
    print("   Buka https://my.telegram.org")
    print("   Login → API Development Tools → Buat aplikasi")
    print()

    api_id = input("Masukkan API ID (angka): ").strip()
    api_hash = input("Masukkan API Hash (teks): ").strip()
    phone = input("Masukkan nomor HP (format: +62xxx): ").strip()

    if not api_id or not api_hash or not phone:
        error("Semua field wajib diisi!")
        return False

    config = {
        "api_id": int(api_id),
        "api_hash": api_hash,
        "phone": phone,
        "bot_username": DEFAULT_BOT,
        "check_interval": 300,
    }
    save_config(config)
    success("Config tersimpan!")

    # Login ke Telegram
    print("\n🔐 Langkah 2: Login ke Telegram")
    client = TelegramClient(str(SESSION_FILE), int(api_id), api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        code = input("   Masukkan kode verifikasi dari Telegram: ").strip()
        try:
            await client.sign_in(phone, code)
        except Exception as e:
            if "password" in str(e).lower():
                password = input("   Masukkan 2FA password: ").strip()
                await client.sign_in(password=password)
            else:
                error(f"Login gagal: {e}")
                return False

    me = await client.get_me()
    await client.disconnect()
    success(f"Login berhasil! Selamat datang {me.first_name} (@{me.username})")

    # Reset state
    save_state({
        "balance_start": 0,
        "ads_claimed": 0,
        "tasks_claimed": 0,
        "total_earned": 0.0,
        "last_run": None,
        "last_ad_claim": None,
        "claimed_ids": [],
    })

    print("""
╔══════════════════════════════════════════════════════════════╗
║       ✅ SETUP SELESAI!                                       ║
╠══════════════════════════════════════════════════════════════╣
║  Jalankan bot:                                                ║
║    python3 bot.py              ← sekali jalan                ║
║    python3 bot.py --loop       ← otomatis terus              ║
║    python3 bot.py --status     ← cek balance                 ║
║                                                              ║
║  Jalankan di background:                                      ║
║    nohup python3 bot.py --loop &                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    return True

# ═══════════════════════════════════════════════════════════════
#  TELEGRAM AUTH
# ═══════════════════════════════════════════════════════════════

async def get_init_data(config: dict) -> str:
    """Dapatkan fresh initData dari Telegram"""
    client = TelegramClient(str(SESSION_FILE), config['api_id'], config['api_hash'])
    await client.connect()

    if not await client.is_user_authorized():
        error("Session expired! Jalankan: python3 bot.py (untuk login ulang)")
        await client.disconnect()
        return ""

    try:
        bot = await client.get_entity(config.get('bot_username', DEFAULT_BOT))
        input_user = types.InputUser(user_id=bot.id, access_hash=bot.access_hash)

        result = await client(functions.messages.RequestMainWebViewRequest(
            peer=bot,
            bot=input_user,
            platform='android',
            theme_params=types.DataJSON(data='{}'),
        ))

        await client.disconnect()

        url = result.url
        fragment = url.split('#')[1]
        tg_data_encoded = fragment.split('&')[0].split('=', 1)[1]
        return unquote(unquote(tg_data_encoded))
    except Exception as e:
        error(f"Gagal get initData: {e}")
        await client.disconnect()
        return ""

# ═══════════════════════════════════════════════════════════════
#  API CLIENT
# ═══════════════════════════════════════════════════════════════

class API:
    def __init__(self, init_data: str):
        self.headers = {
            "Content-Type": "application/json",
            "Origin": API_BASE,
            "Referer": f"{API_BASE}/",
            "X-Telegram-Init-Data": init_data,
            "X-Client-Id": "termux_bot",
        }

    def get(self, path):
        try:
            r = req.get(f"{API_BASE}{path}", headers=self.headers, timeout=15)
            if r.status_code == 200:
                return r.json()
            return {"error": r.text[:200], "status": r.status_code}
        except Exception as e:
            return {"error": str(e)}

    def post(self, path, data=None):
        try:
            r = req.post(f"{API_BASE}{path}", json=data or {}, headers=self.headers, timeout=15)
            if r.status_code == 200:
                return r.json()
            return {"error": r.text[:200], "status": r.status_code}
        except Exception as e:
            return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════
#  BOT LOGIC
# ═══════════════════════════════════════════════════════════════

class Bot:
    def __init__(self, config: dict):
        self.config = config
        self.state = load_state()
        self.api = None

    def refresh(self) -> bool:
        info("🔄 Refreshing auth...")
        data = asyncio.run(get_init_data(self.config))
        if not data:
            return False
        self.api = API(data)
        success("Auth refreshed!")
        return True

    def get_balance(self):
        me = self.api.get("/api/me")
        if "error" in me:
            error(f"Gagal get balance: {me}")
            return None
        return me

    def claim_ads(self):
        total = 0.0
        tasks = self.api.get("/api/tasks")
        if not isinstance(tasks, list):
            return 0.0

        ad_tasks = [t for t in tasks if t['type'] == 'WATCH_AD' and t['status'] == 'ACTIVE']

        for t in ad_tasks:
            r = self.api.post(f"/api/tasks/{t['id']}/claim")
            if r.get('ok'):
                reward = r.get('reward', 0)
                total += reward
                self.state['ads_claimed'] = self.state.get('ads_claimed', 0) + 1
                success(f"🎬 Ad claimed! +{reward}⭐ → Balance: {r.get('balance', '?')}⭐")
            elif 'already_claimed' in str(r) or 'cooldown' in str(r).lower():
                info("⏰ Ad cooldown aktif")
                break
            elif r.get('status') == 401:
                warn("Auth expired, refreshing...")
                if self.refresh():
                    return self.claim_ads()
                return total
            else:
                info(f"Ad result: {r}")
                break
            time.sleep(2)

        return total

    def claim_tasks(self):
        total = 0.0
        tasks = self.api.get("/api/tasks")
        if not isinstance(tasks, list):
            return 0.0

        skip_types = ['WATCH_AD', 'INVITE_FRIENDS', 'SHARE_FRIENDS', 'POST_STORY']
        claimable = [t for t in tasks
                     if t['type'] not in skip_types
                     and t['status'] == 'ACTIVE'
                     and t['id'] not in self.state.get('claimed_ids', [])]

        for t in claimable:
            r = self.api.post(f"/api/tasks/{t['id']}/claim")
            if r.get('ok'):
                reward = r.get('reward', 0)
                total += reward
                self.state['claimed_ids'] = self.state.get('claimed_ids', []) + [t['id']]
                self.state['tasks_claimed'] = self.state.get('tasks_claimed', 0) + 1
                success(f"📋 Task '{t['titleEn']}' claimed! +{reward}⭐")
            elif 'already_claimed' in str(r):
                self.state['claimed_ids'] = self.state.get('claimed_ids', []) + [t['id']]
            time.sleep(2)

        return total

    def run_once(self):
        info("=" * 40)
        info("⭐ RUNNING CYCLE")

        if not self.refresh():
            return

        me = self.get_balance()
        if not me:
            return

        info(f"💰 Balance: {me['balance']}⭐ | Earned: {me['earned']}⭐")

        if self.state.get('balance_start', 0) == 0:
            self.state['balance_start'] = me['balance']

        ads = self.claim_ads()
        tasks = self.claim_tasks()
        total = ads + tasks

        self.state['total_earned'] = self.state.get('total_earned', 0) + total
        self.state['last_run'] = datetime.now().isoformat()
        save_state(self.state)

        me2 = self.get_balance()
        if me2:
            info(f"💰 Final Balance: {me2['balance']}⭐")
        info(f"📊 Earned this run: +{total}⭐ | All time: +{self.state['total_earned']:.1f}⭐")

    def run_loop(self):
        interval = self.config.get('check_interval', 300)
        info(f"🔄 Starting loop (interval: {interval}s)")

        while True:
            try:
                self.run_once()
                info(f"💤 Next check dalam {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                info("Bot stopped!")
                break
            except FloodWaitError as e:
                warn(f"Rate limit! Tunggu {e.seconds}s")
                time.sleep(e.seconds)
            except Exception as e:
                error(f"Error: {e}")
                time.sleep(60)

    def show_status(self):
        if not self.refresh():
            return
        me = self.get_balance()
        if not me:
            return
        s = self.state
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ⭐ BOT STATUS ⭐                          ║
╠══════════════════════════════════════════════════════════════╣
║  Name       : {me['firstName']:<20} (@{me.get('username', 'N/A'):<15})    ║
║  Balance    : {me['balance']:<10} ⭐                               ║
║  Total Earned: {me['earned']:<10} ⭐                               ║
║  Friends    : {me['friends']['amount']:<10}                              ║
║  Ads Claimed: {s.get('ads_claimed', 0):<10}                              ║
║  Tasks Done : {s.get('tasks_claimed', 0):<10}                              ║
║  Last Run   : {str(s.get('last_run', 'Never'))[:19]:<19}            ║
╚══════════════════════════════════════════════════════════════╝
""")

# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    # Setup mode
    if '--setup' in sys.argv or not CONFIG_FILE.exists():
        asyncio.run(setup_wizard())
        return

    config = load_config()
    bot = Bot(config)

    if '--status' in sys.argv:
        bot.show_status()
    elif '--loop' in sys.argv:
        bot.run_loop()
    else:
        bot.run_once()

if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════
#  TERMUX BACKGROUND TIPS
# ═══════════════════════════════════════════════════════════════
#  nohup gak work di Termux. Pakai cara ini:
#
#  Cara 1: termux-wake-lock + screen (PALING GAMPANG)
#    termux-wake-lock
#    screen -S bot
#    python3 bot.py --loop
#    Ctrl+A, D (untuk detach)
#    Tutup Termux aja, bot tetap jalan!
#
#  Cara 2: tmux
#    tmux new -s bot
#    python3 bot.py --loop
#    Ctrl+B, D (untuk detach)
#    tmux attach -t bot (untuk balik)
#
#  Cara 3: Termux:Boot (auto start saat HP nyala)
#    Install Termux:Boot dari F-Droid
#    Buat file ~/.termux/boot/start-bot.sh:
#      #!/data/data/com.termux/files/usr/bin/sh
#      termux-wake-lock
#      cd ~/bintang-auto-bot
#      python3 bot.py --loop &
#    chmod +x ~/.termux/boot/start-bot.sh
# ═══════════════════════════════════════════════════════════════
