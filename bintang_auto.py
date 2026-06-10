#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║       ⭐ BINTANG AUTO BOT v2 - FULL AUTO ⭐                   ║
║  API: https://spinhub.cc/api                                 ║
║  Auto claim ads, auto tasks, auto subscribe channels         ║
║  Berjalan 24/7 di background tanpa buka HP/PC               ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import sys
import logging
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

# ═══════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bintang_auto.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('BintangBot')

# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════

CONFIG_FILE = Path(__file__).parent / "config.json"
STATE_FILE = Path(__file__).parent / "state.json"
API_BASE = "https://spinhub.cc"


def load_config() -> dict:
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        "ads_claimed_total": 0,
        "tasks_completed_total": 0,
        "total_earned": 0.0,
        "last_ad_claim": None,
        "last_full_run": None,
        "subscribed_channels": [],
        "claimed_task_ids": [],
    }


def save_state(state: dict):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════
#  TELEGRAM AUTH - Get fresh initData
# ═══════════════════════════════════════════════════════════════

async def get_fresh_init_data(config: dict) -> str:
    """Dapatkan fresh initData dari Telegram via MTProto API"""
    from telethon import TelegramClient
    from telethon.tl import functions, types

    session_file = Path(__file__).parent / "session"
    client = TelegramClient(
        str(session_file),
        config['api_id'],
        config['api_hash']
    )
    await client.connect()

    if not await client.is_user_authorized():
        logger.error("Telegram session expired! Jalankan ulang untuk login.")
        await client.disconnect()
        return ""

    bot = await client.get_entity(config.get('bot_username', 'EarnStarsAppBot'))
    input_user = types.InputUser(user_id=bot.id, access_hash=bot.access_hash)

    result = await client(functions.messages.RequestMainWebViewRequest(
        peer=bot,
        bot=input_user,
        platform='android',
        theme_params=types.DataJSON(data='{}'),
    ))

    await client.disconnect()

    # Extract initData from URL fragment
    url = result.url
    fragment = url.split('#')[1]
    tg_data_encoded = fragment.split('&')[0].split('=', 1)[1]
    return unquote(unquote(tg_data_encoded))


# ═══════════════════════════════════════════════════════════════
#  API CLIENT
# ═══════════════════════════════════════════════════════════════

class EarnStarsAPI:
    def __init__(self, init_data: str):
        self.init_data = init_data
        self.headers = {
            "Content-Type": "application/json",
            "Origin": API_BASE,
            "Referer": f"{API_BASE}/",
            "X-Telegram-Init-Data": init_data,
            "X-Client-Id": "bintang_auto_bot",
        }

    def _get(self, path: str) -> dict:
        try:
            resp = requests.get(f"{API_BASE}{path}", headers=self.headers, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                return {"error": "unauthorized", "status": 401}
            else:
                return {"error": resp.text[:200], "status": resp.status_code}
        except Exception as e:
            return {"error": str(e)}

    def _post(self, path: str, data: dict = None) -> dict:
        try:
            resp = requests.post(f"{API_BASE}{path}", json=data or {}, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                return {"error": "unauthorized", "status": 401}
            else:
                return {"error": resp.text[:200], "status": resp.status_code}
        except Exception as e:
            return {"error": str(e)}

    def get_me(self) -> dict:
        return self._get("/api/me")

    def get_tasks(self) -> list:
        result = self._get("/api/tasks")
        return result if isinstance(result, list) else []

    def claim_task(self, task_id: int) -> dict:
        return self._post(f"/api/tasks/{task_id}/claim")

    def activate_boost(self) -> dict:
        return self._post("/api/me/boost/activate")

    def get_giveaway(self) -> dict:
        return self._get("/api/giveaway/current")


# ═══════════════════════════════════════════════════════════════
#  TELEGRAM CHANNEL JOINER
# ═══════════════════════════════════════════════════════════════

async def join_channel(config: dict, channel_username: str) -> bool:
    """Join Telegram channel via user API"""
    try:
        from telethon import TelegramClient
        from telethon.tl.functions.channels import JoinChannelRequest

        session_file = Path(__file__).parent / "session"
        client = TelegramClient(str(session_file), config['api_id'], config['api_hash'])
        await client.connect()

        entity = await client.get_entity(channel_username)
        await client(JoinChannelRequest(entity))
        await client.disconnect()
        logger.info(f"  ✓ Joined @{channel_username}")
        return True
    except Exception as e:
        logger.warning(f"  ✗ Gagal join @{channel_username}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
#  MAIN BOT
# ═══════════════════════════════════════════════════════════════

class BintangAutoBot:
    def __init__(self, config: dict):
        self.config = config
        self.state = load_state()
        self.api = None

    def refresh_auth(self) -> bool:
        """Refresh auth token dari Telegram"""
        try:
            logger.info("🔄 Refreshing auth dari Telegram...")
            init_data = asyncio.run(get_fresh_init_data(self.config))
            if not init_data:
                logger.error("Gagal mendapatkan initData!")
                return False
            self.api = EarnStarsAPI(init_data)
            logger.info("✓ Auth berhasil di-refresh")
            return True
        except Exception as e:
            logger.error(f"Error refreshing auth: {e}")
            return False

    def show_balance(self):
        """Tampilkan balance"""
        me = self.api.get_me()
        if "error" in me:
            logger.error(f"Gagal get user info: {me}")
            return me
        logger.info(f"💰 Balance: {me['balance']}⭐ | Earned: {me['earned']}⭐ | Friends: {me['friends']['amount']}")
        return me

    def claim_ads(self) -> float:
        """Auto claim semua iklan yang tersedia"""
        total_claimed = 0.0
        tasks = self.api.get_tasks()
        ad_tasks = [t for t in tasks if t['type'] == 'WATCH_AD' and t['status'] == 'ACTIVE']

        for task in ad_tasks:
            task_id = task['id']
            logger.info(f"🎬 Claiming ad: {task['titleEn']} (+{task['reward']}⭐)")

            result = self.api.claim_task(task_id)
            if result.get('ok'):
                reward = result.get('reward', 0)
                balance = result.get('balance', 0)
                total_claimed += reward
                self.state['ads_claimed_total'] = self.state.get('ads_claimed_total', 0) + 1
                logger.info(f"  ✓ Claimed! +{reward}⭐ → Balance: {balance}⭐")
            elif 'cooldown' in str(result).lower() or 'wait' in str(result).lower():
                logger.info(f"  ⏰ Cooldown aktif, tunggu nanti")
                break
            elif result.get('error') == 'unauthorized':
                logger.error("  ✗ Auth expired! Refreshing...")
                if self.refresh_auth():
                    return self.claim_ads()
                return total_claimed
            else:
                logger.warning(f"  ✗ Gagal: {result}")
                break

            time.sleep(2)

        return total_claimed

    def claim_open_link_tasks(self) -> float:
        """Auto claim task OPEN_LINK (buka link, lalu claim)"""
        total_claimed = 0.0
        tasks = self.api.get_tasks()
        link_tasks = [t for t in tasks if t['type'] == 'OPEN_LINK' and t['status'] == 'ACTIVE'
                      and t['id'] not in self.state.get('claimed_task_ids', [])]

        for task in link_tasks:
            task_id = task['id']
            logger.info(f"🔗 Claiming link task: {task['titleEn']} (+{task['reward']}⭐)")

            # Try to claim directly
            result = self.api.claim_task(task_id)
            if result.get('ok'):
                reward = result.get('reward', 0)
                total_claimed += reward
                self.state['claimed_task_ids'] = self.state.get('claimed_task_ids', []) + [task_id]
                self.state['tasks_completed_total'] = self.state.get('tasks_completed_total', 0) + 1
                logger.info(f"  ✓ Claimed! +{reward}⭐")
            else:
                logger.info(f"  → Result: {result}")

            time.sleep(2)

        return total_claimed

    def claim_subscribe_tasks(self) -> float:
        """Auto claim task SUBSCRIBE_CHANNEL (join channel, lalu claim)"""
        total_claimed = 0.0
        tasks = self.api.get_tasks()
        sub_tasks = [t for t in tasks if t['type'] == 'SUBSCRIBE_CHANNEL' and t['status'] == 'ACTIVE'
                     and t['id'] not in self.state.get('claimed_task_ids', [])]

        for task in sub_tasks:
            task_id = task['id']
            logger.info(f"📢 Claiming subscribe task: {task['titleEn']} (+{task['reward']}⭐)")

            # Try to claim directly (sometimes works without actually joining)
            result = self.api.claim_task(task_id)
            if result.get('ok'):
                reward = result.get('reward', 0)
                total_claimed += reward
                self.state['claimed_task_ids'] = self.state.get('claimed_task_ids', []) + [task_id]
                self.state['tasks_completed_total'] = self.state.get('tasks_completed_total', 0) + 1
                logger.info(f"  ✓ Claimed! +{reward}⭐")
            else:
                logger.info(f"  → Result: {result}")

            time.sleep(2)

        return total_claimed

    def run_full_cycle(self):
        """Jalankan satu siklus penuh"""
        logger.info("=" * 50)
        logger.info("⭐ STARTING FULL CYCLE")
        logger.info("=" * 50)

        # Refresh auth
        if not self.refresh_auth():
            return

        # Show balance
        me = self.show_balance()
        if "error" in me:
            return

        # Claim ads
        ads_earned = self.claim_ads()
        logger.info(f"🎬 Ads earned: {ads_earned}⭐")

        # Claim open link tasks
        links_earned = self.claim_open_link_tasks()
        logger.info(f"🔗 Link tasks earned: {links_earned}⭐")

        # Claim subscribe tasks
        subs_earned = self.claim_subscribe_tasks()
        logger.info(f"📢 Subscribe tasks earned: {subs_earned}⭐")

        # Total
        total = ads_earned + links_earned + subs_earned
        self.state['total_earned'] = self.state.get('total_earned', 0) + total
        self.state['last_full_run'] = datetime.now().isoformat()
        save_state(self.state)

        # Show final balance
        me = self.api.get_me()
        if "error" not in me:
            logger.info(f"💰 Final Balance: {me['balance']}⭐")
            logger.info(f"📊 Total earned this run: {total}⭐")
            logger.info(f"📊 Total earned all time: {self.state['total_earned']}⭐")

    def run_loop(self):
        """Jalankan terus menerus"""
        interval = self.config.get('settings', {}).get('check_interval_seconds', 300)
        logger.info(f"🔄 Starting auto loop (interval: {interval}s)")

        while True:
            try:
                self.run_full_cycle()
                logger.info(f"💤 Next check dalam {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(60)


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║       ⭐ BINTANG AUTO BOT v2 ⭐                               ║
║       @EarnStarsAppBot - Full Auto 24/7                      ║
║       API: https://spinhub.cc/api                            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    config = load_config()
    bot = BintangAutoBot(config)

    if '--once' in sys.argv:
        bot.run_full_cycle()
    elif '--status' in sys.argv:
        if bot.refresh_auth():
            bot.show_balance()
    else:
        bot.run_loop()


if __name__ == "__main__":
    main()
