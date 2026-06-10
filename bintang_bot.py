#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          BINTANG AUTO BOT - Earn Stars Automation            ║
║  Auto claim, auto watch ads, auto referral untuk @earn_stars_bot ║
╚══════════════════════════════════════════════════════════════╝

Cara pakai:
1. Install dependencies: pip install requests colorama
2. Extract auth data dari Telegram Web (lihat README.md)
3. Edit config.json dengan data auth lo
4. Jalankan: python3 bintang_bot.py
"""

import json
import time
import hashlib
import hmac
import urllib.parse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("[!] Install requests: pip install requests")
    sys.exit(1)

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS = True
except ImportError:
    COLORS = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = ""

# ═══════════════════════════════════════════════════════════════
#  KONFIGURASI
# ═══════════════════════════════════════════════════════════════

# Bot token dari @earn_stars_bot (diperlukan untuk validasi auth)
# Bisa didapat dari: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
# Atau dari network tab saat mini app dibuka
BOT_TOKEN = ""  # ISI INI kalau tau bot token-nya

# API Base URL - endpoint backend Earn Stars
# Ini bisa didapat dari Network tab DevTools saat buka mini app
API_BASE = ""  # Contoh: "https://api.earnstars.bot" atau domain lain

# Telegram Bot API URL
TG_API = "https://api.telegram.org"

# ═══════════════════════════════════════════════════════════════
#  WARNA CONSOLE
# ═══════════════════════════════════════════════════════════════

def log_success(msg):
    print(f"{Fore.GREEN}[✓] {msg}{Style.RESET_ALL}")

def log_error(msg):
    print(f"{Fore.RED}[✗] {msg}{Style.RESET_ALL}")

def log_info(msg):
    print(f"{Fore.CYAN}[i] {msg}{Style.RESET_ALL}")

def log_warn(msg):
    print(f"{Fore.YELLOW}[!] {msg}{Style.RESET_ALL}")

def log_task(msg):
    print(f"{Fore.MAGENTA}[★] {msg}{Style.RESET_ALL}")

def log_cooldown(msg):
    print(f"{Fore.YELLOW}[⏰] {msg}{Style.RESET_ALL}")

def banner():
    print(f"""{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║          ⭐ BINTANG AUTO BOT ⭐                              ║
║          Earn Stars Telegram Automation                      ║
║          Auto Claim | Auto Ads | Auto Referral               ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")

# ═══════════════════════════════════════════════════════════════
#  VALIDASI AUTH DATA
# ═══════════════════════════════════════════════════════════════

def validate_init_data(init_data: str, bot_token: str) -> bool:
    """
    Validasi Telegram Mini App initData menggunakan bot token.
    initData format: query_id=...&user=...&auth_date=...&hash=...
    """
    if not bot_token:
        log_warn("Bot token tidak diisi, skip validasi auth")
        return True

    try:
        parsed = urllib.parse.parse_qs(init_data)
        hash_val = parsed.get("hash", [""])[0]

        if not hash_val:
            log_error("Hash tidak ditemukan di initData")
            return False

        # Buat data check string (semua field kecuali hash, sorted)
        data_check_pairs = []
        for key, value in sorted(parsed.items()):
            if key != "hash":
                data_check_pairs.append(f"{key}={value[0]}")
        data_check_string = "\n".join(data_check_pairs)

        # Hitung HMAC-SHA256
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if calculated_hash == hash_val:
            log_success("Auth data valid!")
            return True
        else:
            log_error("Auth data INVALID - hash mismatch")
            return False

    except Exception as e:
        log_error(f"Validasi error: {e}")
        return False


def parse_user_data(init_data: str) -> dict:
    """Parse user data dari initData"""
    try:
        parsed = urllib.parse.parse_qs(init_data)
        user_json = parsed.get("user", ["{}"])[0]
        user = json.loads(user_json)
        return {
            "id": user.get("id"),
            "first_name": user.get("first_name", ""),
            "username": user.get("username", ""),
            "language_code": user.get("language_code", ""),
        }
    except:
        return {}


# ═══════════════════════════════════════════════════════════════
#  API CLIENT
# ═══════════════════════════════════════════════════════════════

class EarnStarsAPI:
    """
    Client untuk berinteraksi dengan API backend Earn Stars.

    ⚠️ ENDPOINT INI PERLU DIISI DARI NETWORK TAB!
    Cara capture:
    1. Buka Chrome/Kiwi Browser
    2. Install extension "Bypass Telegram Web"
    3. Buka Mini App @earn_stars_bot
    4. Buka DevTools → Network tab
    5. Filter: XHR/Fetch
    6. Lakukan action (watch ads, claim, dll)
    7. Catat URL dan headers yang dipake
    """

    def __init__(self, query_id: str, user_data: str, hash_val: str,
                 bearer_token: str = "", api_base: str = ""):
        self.query_id = query_id
        self.user_data = user_data
        self.hash = hash_val
        self.bearer_token = bearer_token
        self.api_base = api_base or API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://telegram.org",
            "Referer": "https://telegram.org/",
        })
        if self.bearer_token:
            self.session.headers["Authorization"] = f"Bearer {self.bearer_token}"

    def _build_init_data(self) -> str:
        """Build initData string untuk autentikasi"""
        return (
            f"query_id={self.query_id}"
            f"&user={urllib.parse.quote(self.user_data)}"
            f"&auth_date={int(time.time())}"
            f"&hash={self.hash}"
        )

    def _request(self, method: str, endpoint: str, data: dict = None,
                 extra_headers: dict = None) -> dict:
        """Generic API request"""
        url = f"{self.api_base}{endpoint}"
        headers = extra_headers or {}

        try:
            if method.upper() == "GET":
                resp = self.session.get(url, params=data, headers=headers, timeout=30)
            else:
                resp = self.session.post(url, json=data, headers=headers, timeout=30)

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            log_error(f"HTTP Error {resp.status_code}: {resp.text[:200]}")
            return {"error": str(e), "status": resp.status_code}
        except requests.exceptions.RequestException as e:
            log_error(f"Request Error: {e}")
            return {"error": str(e)}

    # ─── AUTH ─────────────────────────────────────────────────

    def authenticate(self) -> dict:
        """
        Autentikasi dengan initData untuk mendapatkan session token.
        Endpoint ini perlu di-capture dari Network tab.
        """
        init_data = self._build_init_data()

        # ⚠️ GANTI ENDPOINT INI DARI NETWORK TAB
        # Kemungkinan endpoint:
        # POST /api/auth/login
        # POST /api/user/auth
        # POST /auth/telegram
        # POST /api/v1/auth
        result = self._request("POST", "/api/auth/login", {
            "initData": init_data,
            "query_id": self.query_id,
        })

        if "token" in result:
            self.bearer_token = result["token"]
            self.session.headers["Authorization"] = f"Bearer {self.bearer_token}"
            log_success(f"Auth berhasil! Token: {self.bearer_token[:20]}...")
        elif "error" not in result:
            log_success("Auth berhasil!")

        return result

    # ─── USER INFO ────────────────────────────────────────────

    def get_user_info(self) -> dict:
        """Ambil info user (balance, tasks, dll)"""
        # ⚠️ GANTI ENDPOINT
        # Kemungkinan: GET /api/user, GET /api/user/info, GET /api/me
        return self._request("GET", "/api/user/info")

    def get_balance(self) -> float:
        """Ambil balance stars"""
        info = self.get_user_info()
        # Field name mungkin: stars, balance, amount, points
        return info.get("stars", info.get("balance", 0))

    # ─── TASKS ────────────────────────────────────────────────

    def get_tasks(self) -> list:
        """Ambil daftar task yang tersedia"""
        # ⚠️ GANTI ENDPOINT
        # Kemungkinan: GET /api/tasks, GET /api/task/list
        result = self._request("GET", "/api/tasks")
        return result if isinstance(result, list) else result.get("tasks", [])

    def complete_task(self, task_id: str) -> dict:
        """Selesaikan task"""
        # ⚠️ GANTI ENDPOINT
        # Kemungkinan: POST /api/tasks/{id}/complete, POST /api/task/claim
        return self._request("POST", f"/api/tasks/{task_id}/complete", {
            "task_id": task_id,
        })

    def claim_task_reward(self, task_id: str) -> dict:
        """Claim reward setelah task selesai"""
        # ⚠️ GANTI ENDPOINT
        return self._request("POST", f"/api/tasks/{task_id}/claim", {
            "task_id": task_id,
        })

    # ─── ADS ──────────────────────────────────────────────────

    def watch_ad(self) -> dict:
        """
        Watch iklan untuk mendapatkan stars.
        Biasanya ada endpoint khusus untuk ad watching.
        """
        # ⚠️ GANTI ENDPOINT
        # Kemungkinan: POST /api/ads/watch, POST /api/ad/claim
        return self._request("POST", "/api/ads/watch", {
            "type": "short",
        })

    def get_ad_status(self) -> dict:
        """Cek status iklan (available/cooldown)"""
        # ⚠️ GANTI ENDPOINT
        return self._request("GET", "/api/ads/status")

    def claim_ad_reward(self) -> dict:
        """Claim reward setelah nonton iklan"""
        # ⚠️ GANTI ENDPOINT
        return self._request("POST", "/api/ads/claim")

    # ─── REFERRAL ─────────────────────────────────────────────

    def get_referral_info(self) -> dict:
        """Ambil info referral (kode, link, jumlah referral)"""
        # ⚠️ GANTI ENDPOINT
        return self._request("GET", "/api/referral/info")

    def get_referral_link(self) -> str:
        """Ambil link referral"""
        info = self.get_referral_info()
        return info.get("link", info.get("referral_url", ""))

    def apply_referral(self, code: str) -> dict:
        """Gunakan kode referral"""
        # ⚠️ GANTI ENDPOINT
        return self._request("POST", "/api/referral/apply", {
            "code": code,
        })


# ═══════════════════════════════════════════════════════════════
#  STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

class BotState:
    """Track bot state untuk cooldown dan task progress"""

    def __init__(self, state_file: str = "bot_state.json"):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict:
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "last_ad_watch": None,
                "last_task_check": None,
                "completed_tasks": [],
                "total_earned": 0,
                "ads_watched": 0,
                "sessions": 0,
            }

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    def is_ad_cooldown_done(self, cooldown_seconds: int = 7200) -> bool:
        """Cek apakah cooldown iklan sudah selesai (default 2 jam)"""
        last = self.state.get("last_ad_watch")
        if not last:
            return True
        last_time = datetime.fromisoformat(last)
        return datetime.now() >= last_time + timedelta(seconds=cooldown_seconds)

    def get_cooldown_remaining(self, cooldown_seconds: int = 7200) -> int:
        """Sisa cooldown dalam detik"""
        last = self.state.get("last_ad_watch")
        if not last:
            return 0
        last_time = datetime.fromisoformat(last)
        remaining = (last_time + timedelta(seconds=cooldown_seconds)) - datetime.now()
        return max(0, int(remaining.total_seconds()))

    def mark_ad_watched(self):
        """Tandai iklan sudah ditonton"""
        self.state["last_ad_watch"] = datetime.now().isoformat()
        self.state["ads_watched"] = self.state.get("ads_watched", 0) + 1
        self.save()

    def mark_task_done(self, task_id: str, earned: float = 0):
        """Tandai task selesai"""
        if task_id not in self.state["completed_tasks"]:
            self.state["completed_tasks"].append(task_id)
        self.state["total_earned"] = self.state.get("total_earned", 0) + earned
        self.save()


# ═══════════════════════════════════════════════════════════════
#  MAIN BOT LOGIC
# ═══════════════════════════════════════════════════════════════

class BintangBot:
    """Bot utama untuk auto claim Earn Stars"""

    def __init__(self, account_config: dict, settings: dict):
        self.config = account_config
        self.settings = settings
        self.name = account_config.get("name", "Unknown")
        self.state = BotState(f"state_{self.name.replace(' ', '_')}.json")

        # Build initData string
        self.init_data = (
            f"query_id={account_config['query_id']}"
            f"&user={urllib.parse.quote(account_config['user_data'])}"
            f"&auth_date={int(time.time())}"
            f"&hash={account_config['hash']}"
        )

        self.api = EarnStarsAPI(
            query_id=account_config["query_id"],
            user_data=account_config["user_data"],
            hash_val=account_config["hash"],
        )

    def login(self) -> bool:
        """Login dan validasi session"""
        log_info(f"[{self.name}] Melakukan autentikasi...")

        # Validasi auth data
        if BOT_TOKEN:
            if not validate_init_data(self.init_data, BOT_TOKEN):
                log_error(f"[{self.name}] Auth data tidak valid!")
                return False

        # Authenticate dengan backend
        result = self.api.authenticate()
        if "error" in result and result.get("status") in [401, 403]:
            log_error(f"[{self.name}] Auth gagal: {result}")
            return False

        log_success(f"[{self.name}] Login berhasil!")

        # Tampilkan info user
        user_info = self.api.get_user_info()
        if user_info and "error" not in user_info:
            balance = user_info.get("stars", user_info.get("balance", "?"))
            log_info(f"[{self.name}] Balance: {balance} ⭐")

        return True

    def do_tasks(self):
        """Auto complete semua task yang tersedia"""
        if not self.settings.get("auto_claim_rewards", True):
            return

        log_task(f"[{self.name}] Checking tasks...")
        tasks = self.api.get_tasks()

        if not tasks:
            log_info(f"[{self.name}] Tidak ada task tersedia")
            return

        completed = self.state.state.get("completed_tasks", [])
        new_tasks = 0

        for task in tasks:
            task_id = str(task.get("id", ""))
            task_name = task.get("name", task.get("title", "Unknown"))
            task_status = task.get("status", "")

            # Skip task yang sudah selesai
            if task_id in completed or task_status in ["completed", "done", "claimed"]:
                continue

            log_task(f"[{self.name}] Menyelesaikan: {task_name}")

            # Complete task
            result = self.api.complete_task(task_id)
            if "error" not in result:
                # Claim reward
                claim = self.api.claim_task_reward(task_id)
                earned = claim.get("stars", claim.get("reward", 0))
                self.state.mark_task_done(task_id, earned)
                log_success(f"[{self.name}] Task '{task_name}' selesai! +{earned} ⭐")
                new_tasks += 1

            # Delay antar task
            time.sleep(self.settings.get("delay_between_actions", 5))

        if new_tasks == 0:
            log_info(f"[{self.name}] Semua task sudah selesai")
        else:
            log_success(f"[{self.name}] {new_tasks} task baru diselesaikan!")

    def do_watch_ads(self):
        """Auto watch ads (dengan cooldown 2 jam)"""
        if not self.settings.get("auto_watch_ads", True):
            return

        cooldown = self.settings.get("cooldown_seconds", 7200)

        # Cek cooldown
        if not self.state.is_ad_cooldown_done(cooldown):
            remaining = self.state.get_cooldown_remaining(cooldown)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            log_cooldown(
                f"[{self.name}] Cooldown aktif. "
                f"Sisa: {hours}h {minutes}m"
            )
            return

        log_task(f"[{self.name}] Watching ads...")

        # Cek status iklan
        ad_status = self.api.get_ad_status()
        if ad_status.get("available") == False:
            log_warn(f"[{self.name}] Iklan tidak tersedia saat ini")
            return

        # Watch dan claim iklan
        ads_watched = 0
        max_ads = 10  # Biasanya ada limit per sesi

        for i in range(max_ads):
            result = self.api.watch_ad()
            if "error" in result:
                if result.get("status") == 429:
                    log_warn(f"[{self.name}] Kuota iklan habis, cooldown dimulai")
                    break
                log_error(f"[{self.name}] Gagal watch ad: {result}")
                break

            # Claim reward
            claim = self.api.claim_ad_reward()
            earned = claim.get("stars", claim.get("reward", 0))
            ads_watched += 1
            log_success(f"[{self.name}] Ad {ads_watched}: +{earned} ⭐")

            # Delay antar iklan
            time.sleep(self.settings.get("delay_between_actions", 5))

        if ads_watched > 0:
            self.state.mark_ad_watched()
            log_success(f"[{self.name}] Total {ads_watched} iklan ditonton!")
        else:
            log_info(f"[{self.name}] Tidak ada iklan yang bisa ditonton")

    def do_referral(self):
        """Auto referral (gunakan kode referral jika ada)"""
        if not self.settings.get("auto_referral", False):
            return

        ref_code = self.config.get("referral_code", "")
        if not ref_code or ref_code == "PASTE_REFERRAL_CODE_DISINI":
            return

        log_info(f"[{self.name}] Menerapkan referral code: {ref_code}")
        result = self.api.apply_referral(ref_code)
        if "error" not in result:
            log_success(f"[{self.name}] Referral berhasil diterapkan!")
        else:
            log_warn(f"[{self.name}] Referral: {result.get('error', 'sudah pernah')}")

    def show_status(self):
        """Tampilkan status bot"""
        s = self.state.state
        cooldown = self.settings.get("cooldown_seconds", 7200)
        remaining = self.state.get_cooldown_remaining(cooldown)

        print(f"\n{'='*50}")
        print(f"  {Fore.CYAN}STATUS: {self.name}{Style.RESET_ALL}")
        print(f"{'='*50}")
        print(f"  Ads watched     : {s.get('ads_watched', 0)}")
        print(f"  Tasks completed : {len(s.get('completed_tasks', []))}")
        print(f"  Total earned    : {s.get('total_earned', 0):.2f} ⭐")
        print(f"  Sessions        : {s.get('sessions', 0)}")

        if remaining > 0:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            print(f"  Cooldown        : {hours}h {minutes}m remaining")
        else:
            print(f"  Cooldown        : {Fore.GREEN}Ready!{Style.RESET_ALL}")

        print(f"{'='*50}\n")

    def run_once(self):
        """Jalankan sekali (semua task)"""
        self.state.state["sessions"] = self.state.state.get("sessions", 0) + 1
        self.state.save()

        self.show_status()
        self.do_tasks()
        self.do_watch_ads()
        self.do_referral()

    def run_loop(self):
        """Jalankan terus menerus"""
        interval = self.settings.get("check_interval_seconds", 60)
        log_success(f"[{self.name}] Bot started! Check setiap {interval}s")

        while True:
            try:
                self.run_once()
                log_info(f"[{self.name}] Next check dalam {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                log_info(f"\n[{self.name}] Bot stopped by user")
                break
            except Exception as e:
                log_error(f"[{self.name}] Error: {e}")
                time.sleep(30)


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    banner()

    # Load config
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        log_error(f"Config tidak ditemukan: {config_path}")
        log_info("Buat config.json dari template yang tersedia")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    accounts = config.get("accounts", [])
    settings = config.get("settings", {})

    if not accounts:
        log_error("Tidak ada akun di config.json!")
        sys.exit(1)

    # Validate config
    for acc in accounts:
        if acc.get("query_id", "").startswith("PASTE"):
            log_error(f"Akun '{acc.get('name')}' belum diisi auth data!")
            log_info("Edit config.json dengan data dari Telegram Web")
            sys.exit(1)

    log_info(f"Loaded {len(accounts)} akun")

    # Single account mode
    if len(accounts) == 1:
        bot = BintangBot(accounts[0], settings)
        if bot.login():
            if "--loop" in sys.argv:
                bot.run_loop()
            else:
                bot.run_once()
        return

    # Multi account mode
    bots = []
    for acc in accounts:
        bot = BintangBot(acc, settings)
        if bot.login():
            bots.append(bot)

    if not bots:
        log_error("Tidak ada akun yang berhasil login!")
        sys.exit(1)

    if "--loop" in sys.argv:
        log_success(f"Running {len(bots)} akun dalam loop...")
        while True:
            try:
                for bot in bots:
                    bot.run_once()
                interval = settings.get("check_interval_seconds", 60)
                log_info(f"Next check dalam {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                log_info("\nBot stopped by user")
                break
    else:
        for bot in bots:
            bot.run_once()


if __name__ == "__main__":
    main()
