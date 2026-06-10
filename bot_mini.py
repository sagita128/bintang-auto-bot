#!/usr/bin/env python3
"""⭐ Bintang Auto Bot - @EarnStarsAppBot - Auto claim ads & tasks"""
import asyncio,json,sys,os,time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
try:
 from telethon import TelegramClient
 from telethon.tl import functions, types
 import requests as req
except ImportError:
 print("Install: pip install telethon requests");sys.exit(1)

D=Path(__file__).parent
BASE_URL="https://spinhub.cc"
BOT_NAME="EarnStarsAppBot"

def log(m):print(f"[{datetime.now():%H:%M:%S}] {m}")

def get_config():
 f=D/"config.json"
 if f.exists():
  with open(f) as x:return json.load(x)
 return {}

def save_config(c):
 with open(D/"config.json","w") as x:json.dump(c,x,indent=2)

def get_state():
 f=D/"state.json"
 if f.exists():
  try:
   with open(f) as x:return json.load(x)
  except:pass
 return {"ads":0,"tasks":0,"earned":0,"ids":[]}

def save_state(s):
 with open(D/"state.json","w") as x:json.dump(s,x,indent=2,default=str)

async def get_init(cfg):
 c=TelegramClient(str(D/"session"),cfg["api_id"],cfg["api_hash"])
 await c.connect()
 if not await c.is_user_authorized():
  await c.disconnect();return ""
 b=await c.get_entity(cfg.get("bot",BOT_NAME))
 r=await c(functions.messages.RequestMainWebViewRequest(peer=b,bot=types.InputUser(user_id=b.id,access_hash=b.access_hash),platform="android",theme_params=types.DataJSON(data="{}")))
 await c.disconnect()
 u=r.url.split("#")[1].split("&")[0].split("=",1)[1]
 return unquote(unquote(u))

class API:
 def __init__(s,d):s.h={"Content-Type":"application/json","Origin":BASE_URL,"Referer":f"{BASE_URL}/","X-Telegram-Init-Data":d,"X-Client-Id":"bot"}
 def get(s,p):
  try:r=req.get(f"{BASE_URL}{p}",headers=s.h,timeout=15);return r.json() if r.status_code==200 else {"error":r.text[:100]}
  except Exception as e:return {"error":str(e)}
 def post(s,p,d=None):
  try:r=req.post(f"{BASE_URL}{p}",json=d or {},headers=s.h,timeout=15);return r.json() if r.status_code==200 else {"error":r.text[:100]}
  except Exception as e:return {"error":str(e)}

def run():
 cfg=get_config()
 if not cfg or "--setup" in sys.argv:
  print("⭐ SETUP WIZARD")
  aid=input("API ID (dari my.telegram.org): ").strip()
  ahash=input("API Hash: ").strip()
  phone=input("Nomor HP (+62xxx): ").strip()
  cfg={"api_id":int(aid),"api_hash":ahash,"phone":phone,"bot":BOT_NAME,"interval":300}
  save_config(cfg)
  async def login():
   c=TelegramClient(str(D/"session"),int(aid),ahash)
   await c.connect()
   await c.send_code_request(phone)
   code=input("Kode verifikasi: ").strip()
   try:await c.sign_in(phone,code)
   except:
    pw=input("2FA password: ").strip();await c.sign_in(password=pw)
   m=await c.get_me();await c.disconnect()
   print(f"✅ Login: {m.first_name} (@{m.username})")
  asyncio.run(login())
  save_state({"ads":0,"tasks":0,"earned":0,"ids":[]})
  print("✅ Setup selesai! Jalankan: python3 bot.py --loop");return

 st=get_state()
 log("🔄 Refreshing auth...")
 d=asyncio.run(get_init(cfg))
 if not d:log("❌ Auth gagal!");return
 a=API(d)
 me=a.get("/api/me")
 if "error" in me:log(f"❌ {me}");return
 log(f"💰 {me['balance']}⭐ | Earned: {me['earned']}⭐")

 tasks=a.get("/api/tasks")
 if isinstance(tasks,list):
  for t in tasks:
   if t["type"]=="WATCH_AD" and t["status"]=="ACTIVE":
    r=a.post(f"/api/tasks/{t['id']}/claim")
    if r.get("ok"):st["ads"]+=1;log(f"🎬 Ad +{r['reward']}⭐ → {r['balance']}⭐")
    time.sleep(2)
   elif t["type"] not in ["WATCH_AD","INVITE_FRIENDS","SHARE_FRIENDS","POST_STORY"] and t["id"] not in st.get("ids",[]):
    r=a.post(f"/api/tasks/{t['id']}/claim")
    if r.get("ok"):st["tasks"]+=1;st["ids"].append(t["id"]);log(f"📋 {t['titleEn']} +{r['reward']}⭐")
    elif "already_claimed" in str(r):st["ids"].append(t["id"])
    time.sleep(2)

 me2=a.get("/api/me")
 if "error" not in me2:log(f"💰 Final: {me2['balance']}⭐")
 save_state(st)

if __name__=="__main__":
 if "--loop" in sys.argv:
  iv=get_config().get("interval",300)
  print(f"⭐ Auto loop (interval: {iv}s)")
  while True:
   try:run();log(f"💤 Next: {iv}s");time.sleep(iv)
   except KeyboardInterrupt:break
   except Exception as e:log(f"❌ {e}");time.sleep(60)
 elif "--status" in sys.argv:
  run()
 else:
  run()
