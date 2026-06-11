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
from datetime import datetime, timedelta, timezone
import calendar
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
SESSION_FILE = BASE_DIR / "session"  # default, akan di-override oleh config
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
        "session_name": phone.replace('+', '').replace('-', '').replace(' ', ''),
    }
    save_config(config)

    # Simpan juga sebagai config_<session_name>.json untuk multi-account
    account_config = BASE_DIR / f"config_{config['session_name']}.json"
    with open(account_config, 'w') as f:
        json.dump(config, f, indent=2)
    success(f"Config tersimpan! (config.json + {account_config.name})")

    # Login ke Telegram
    print("\n🔐 Langkah 2: Login ke Telegram")
    session_file = BASE_DIR / config['session_name']
    client = TelegramClient(str(session_file), int(api_id), api_hash)

    # Connect dengan retry
    for attempt in range(3):
        try:
            await client.connect()
            break
        except Exception as e:
            if attempt < 2:
                wait = (attempt + 1) * 5
                warn(f"Koneksi gagal (attempt {attempt+1}/3): {e}")
                info(f"Coba lagi dalam {wait} detik...")
                await asyncio.sleep(wait)
            else:
                error(f"Gagal connect ke Telegram setelah 3 percobaan: {e}")
                error("Pastikan koneksi internet stabil, lalu coba lagi nanti.")
                return False

    if not await client.is_user_authorized():
        # Helper untuk nampilin info cara kode dikirim
        def kode_dikirim_via(sent_code):
            tipe = type(sent_code.type).__name__ if sent_code else '?'
            if 'App' in tipe:
                info("📱 Kode dikirim via Telegram App (cek chat Telegram)")
            elif 'Sms' in tipe:
                info("📨 Kode dikirim via SMS (cek SMS biasa di HP)")
            elif 'Call' in tipe:
                info("📞 Kode dikirim via panggilan telepon")
            elif 'Fragment' in tipe:
                info("🔗 Kode dikirim via Fragment")
            else:
                info(f"📬 Kode dikirim via {tipe if tipe != '?' else 'Telegram/SMS'}")

        sent = None
        try:
            sent = await client.send_code_request(phone)
            kode_dikirim_via(sent)
        except FloodWaitError as fwe:
            warn(f"Harus tunggu {fwe.seconds} detik ({fwe.seconds/60:.1f} menit) sebelum minta kode.")
            info("Kalau sebelumnya udah dapet kode, langsung masukin aja.")
        except Exception as e:
            warn(f"Gagal kirim kode: {e}")
            info("Mungkin kode sebelumnya masih berlaku, coba langsung masukin.")

        while True:
            prompt = "   Masukkan kode verifikasi"
            prompt += " (0=kirim ulang, 1=force SMS, kosong=batal): "
            code = input(prompt).strip()

            if code == '':
                info("Setup dibatalkan.")
                return False

            if code == '1':
                info("Mengirim ulang via SMS (force)...")
                try:
                    sent = await client.send_code_request(phone, force_sms=True)
                    kode_dikirim_via(sent)
                except FloodWaitError as fwe:
                    warn(f"Harus tunggu {fwe.seconds} detik ({fwe.seconds/60:.1f} menit) sebelum minta kode baru.")
                    info("Kode sebelumnya masih berlaku, coba masukin yang udah ada.")
                except Exception as e:
                    error(f"Gagal kirim kode: {e}")
                continue

            if code == '0':
                info("Mengirim ulang kode verifikasi...")
                try:
                    sent = await client.send_code_request(phone)
                    kode_dikirim_via(sent)
                except FloodWaitError as fwe:
                    warn(f"Harus tunggu {fwe.seconds} detik ({fwe.seconds/60:.1f} menit) sebelum minta kode baru.")
                    info("Kode sebelumnya masih berlaku, coba masukin yang udah ada.")
                except Exception as e:
                    error(f"Gagal kirim kode: {e}")
                continue

            try:
                await client.sign_in(phone, code)
                break  # Sukses
            except FloodWaitError as fwe:
                warn(f"Terlalu banyak percobaan! Tunggu {fwe.seconds} detik.")
                info("Jalankan ulang setup setelah waktu tersebut.")
                return False
            except Exception as e:
                err_msg = str(e).lower()
                if "password" in err_msg:
                    password = input("   Masukkan 2FA password: ").strip()
                    try:
                        await client.sign_in(password=password)
                        break
                    except Exception as e2:
                        error(f"2FA gagal: {e2}")
                        return False
                elif "invalid" in err_msg or "code" in err_msg:
                    warn(f"Kode verifikasi salah. Coba lagi atau kirim ulang (0).")
                    continue
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
    session_name = config.get('session_name', 'session')
    session_file = BASE_DIR / session_name
    client = TelegramClient(str(session_file), config['api_id'], config['api_hash'])
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
            warn(f"Ads response bukan list: {tasks}")
            return 0.0

        # Cek cooldown dari /api/me (lebih akurat)
        me = self.api.get("/api/me")
        if isinstance(me, dict) and 'adCooldownUntil' in me:
            cd_ms = me['adCooldownUntil']
            now_ms = int(time.time() * 1000)
            if cd_ms is not None and cd_ms > now_ms:
                wait_sec = (cd_ms - now_ms) / 1000
                info(f"⏰ Ad cooldown dari API: {wait_sec:.0f}s ({wait_sec/60:.1f}m)")
                self.state['next_ad_cd_ms'] = cd_ms
                save_state(self.state)
                return total
            else:
                info(f"⏰ Ad cooldown sudah lewat! Bisa claim!")

        ad_tasks = [t for t in tasks if t['type'] == 'WATCH_AD' and t['status'] == 'ACTIVE']
        info(f"🎬 Active ad tasks: {len(ad_tasks)}")

        if not ad_tasks:
            info("🎬 Tidak ada ad task yang aktif")
            return 0.0

        for t in ad_tasks:
            burst_size = t.get('burstSize', 5)
            info(f"🎬 Ad: burstSize={burst_size}, langsung claim...")

            claimed = 0
            for i in range(burst_size):
                info(f"  🎬 Claim #{i+1}...")
                r = self.api.post(f"/api/tasks/{t['id']}/claim")
                if r.get('ok'):
                    reward = r.get('reward', 0)
                    total += reward
                    claimed += 1
                    self.state['ads_claimed'] = self.state.get('ads_claimed', 0) + 1
                    success(f"  ✅ Ad #{claimed}! +{reward}⭐")
                elif r.get('status') == 429 or 'cooldown' in str(r).lower():
                    info(f"  ⏰ Cooldown setelah {claimed} claim")
                    break
                elif r.get('status') == 409 or 'already_claimed' in str(r):
                    info(f"  ⏭ Already claimed")
                    break
                elif r.get('status') == 401:
                    warn("Auth expired, refreshing...")
                    if self.refresh():
                        return self.claim_ads()
                    return total
                else:
                    info(f"  ❌ Result: {r}")
                    break
                time.sleep(5)

            if claimed > 0:
                info(f"🎬 Burst total: {claimed} ads = +{total}⭐")
            else:
                info("🎬 Tidak ada ad yang bisa di-claim (cooldown)")

        save_state(self.state)
        return total

    async def _join_channel(self, username):
        from telethon.tl.functions.channels import JoinChannelRequest
        session_name = self.config.get('session_name', 'session')
        session_file = BASE_DIR / session_name
        client = TelegramClient(str(session_file), self.config['api_id'], self.config['api_hash'])
        await client.connect()
        try:
            entity = await client.get_entity(username)
            await client(JoinChannelRequest(entity))
            info(f"  ✅ Joined @{username}")
        except Exception as e:
            warn(f"  ⚠ Gagal join @{username}: {e}")
        finally:
            await client.disconnect()

    def claim_tasks(self):
        total = 0.0
        tasks = self.api.get("/api/tasks")
        if not isinstance(tasks, list):
            warn(f"Tasks response bukan list: {tasks}")
            return 0.0

        info(f"📋 Total tasks dari API: {len(tasks)}")

        skip_types = ['WATCH_AD', 'INVITE_FRIENDS', 'SHARE_FRIENDS']
        claimed_ids = self.state.get('claimed_ids', [])

        for t in tasks:
            ttype = t.get('type', '?')
            tstatus = t.get('status', '?')
            tid = t.get('id', '?')
            ttitle = t.get('titleEn', t.get('title', '?'))
            target = t.get('target')

            if ttype in skip_types:
                continue
            if tstatus != 'ACTIVE':
                continue
            if tid in claimed_ids:
                continue

            # POST_STORY: coba complete dulu sebelum claim
            if ttype == 'POST_STORY':
                info(f"  📸 Trying complete before claim...")
                for ep in ['complete', 'start', 'verify']:
                    cr = self.api.post(f"/api/tasks/{tid}/{ep}")
                    if cr.get('ok'):
                        info(f"    POST /{ep}: ok")
                        break
                    elif cr.get('status') in (200, 201, 204):
                        info(f"    POST /{ep}: {cr}")
                        break
                    else:
                        info(f"    POST /{ep} returned {cr.get('status')}: {cr.get('error', '?')}")

            # Join channel dulu kalau SUBSCRIBE_CHANNEL
            if ttype == 'SUBSCRIBE_CHANNEL' and target:
                info(f"  📢 Joining @{target}...")
                try:
                    asyncio.run(self._join_channel(target))
                    time.sleep(5)  # Tunggu Telegram sync
                except Exception as e:
                    warn(f"  ⚠ Join gagal: {e}")

            info(f"  🎯 Task '{ttitle}' ({ttype}) target={target}")
            r = self.api.post(f"/api/tasks/{tid}/claim")
            if r.get('ok'):
                reward = r.get('reward', 0)
                total += reward
                self.state['claimed_ids'] = claimed_ids + [tid]
                self.state['tasks_claimed'] = self.state.get('tasks_claimed', 0) + 1
                success(f"  ✅ Task '{ttitle}' claimed! +{reward}⭐")
            elif 'already_claimed' in str(r):
                self.state['claimed_ids'] = claimed_ids + [tid]
                info(f"  ⏭ Task '{ttitle}' already claimed")
            elif 'cooldown' in str(r).lower():
                info(f"  ⏰ Task '{ttitle}' cooldown")
            else:
                warn(f"  ❌ Task '{ttitle}' gagal: {r}")
            time.sleep(2)

        if total == 0:
            info("📋 Tidak ada task baru yang bisa di-claim")
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

        # Sync state dengan API
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
        info(f"📊 Earned this run: +{total}⭐ | API balance: {me.get('balance', '?')}⭐")

    def run_loop(self):
        info(f"🔄 Starting smart loop")

        while True:
            try:
                self.run_once()

                # Hitung interval berdasarkan adCooldownUntil dari /api/me
                me = self.api.get("/api/me")
                wait_sec = 300  # default 5 menit

                if isinstance(me, dict) and 'adCooldownUntil' in me:
                    cd_ms = me['adCooldownUntil']
                    now_ms = int(time.time() * 1000)
                    if cd_ms > now_ms:
                        wait_sec = int((cd_ms - now_ms) / 1000) + 30  # +30s buffer
                        info(f"💤 Ad cooldown: tunggu {wait_sec}s ({wait_sec/60:.1f}m)")
                    else:
                        info(f"💤 Cooldown sudah lewat! Cycle berikutnya 30s")
                        wait_sec = 30
                else:
                    info(f"💤 Tidak ada cooldown info, tunggu {wait_sec}s")

                # Cap at 2 hours
                wait_sec = min(wait_sec, 7200)
                time.sleep(wait_sec)

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
    # List accounts
    if '--list' in sys.argv:
        configs = list(BASE_DIR.glob('config_*.json'))
        if configs:
            info("📱 Akun yang tersedia:")
            for c in configs:
                name = c.stem.replace('config_', '')
                with open(c) as f:
                    cfg = json.load(f)
                info(f"  • {name} ({cfg.get('phone', '?')})")
        else:
            info("Belum ada akun. Jalankan: python3 bot.py --setup")
        return

    # Setup mode
    if '--setup' in sys.argv or not CONFIG_FILE.exists():
        asyncio.run(setup_wizard())
        return

    config = load_config()

    # Support --account flag untuk switch akun
    if '--account' in sys.argv:
        idx = sys.argv.index('--account')
        if idx + 1 < len(sys.argv):
            account_name = sys.argv[idx + 1]
            account_config = BASE_DIR / f"config_{account_name}.json"
            if account_config.exists():
                with open(account_config) as f:
                    config = json.load(f)
                info(f"📱 Switching ke akun: {account_name}")
            else:
                error(f"Config {account_config} tidak ditemukan!")
                return

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
