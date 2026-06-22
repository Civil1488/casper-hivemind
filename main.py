import os
import random
import httpx
import subprocess
import json
import asyncio
import sqlite3
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =====================
# DATABASE
# =====================

def init_db():
    conn = sqlite3.connect("hivemind.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        tasks_done INTEGER DEFAULT 0,
        tasks_correct INTEGER DEFAULT 0,
        reputation INTEGER DEFAULT 0,
        level TEXT DEFAULT 'Beginner',
        wallet TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        task_id INTEGER,
        is_honeypot INTEGER DEFAULT 0,
        correct_answer TEXT,
        user_answer TEXT,
        reward REAL,
        tx_hash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

def get_user(telegram_id):
    conn = sqlite3.connect("hivemind.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "telegram_id": row[0],
            "username": row[1],
            "balance": row[2],
            "tasks_done": row[3],
            "tasks_correct": row[4],
            "reputation": row[5],
            "level": row[6],
            "wallet": row[7]
        }
    return None

def create_user(telegram_id, username):
    wallet = f"casper1{telegram_id}abc{random.randint(1000,9999)}"
    conn = sqlite3.connect("hivemind.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (telegram_id, username, wallet) VALUES (?, ?, ?)",
        (telegram_id, username, wallet)
    )
    conn.commit()
    conn.close()
    return get_user(telegram_id)

def update_user_after_task(telegram_id, reward, is_correct):
    conn = sqlite3.connect("hivemind.db")
    c = conn.cursor()
    c.execute("SELECT tasks_done, tasks_correct, reputation FROM users WHERE telegram_id=?", (telegram_id,))
    row = c.fetchone()
    tasks_done = row[0] + 1
    tasks_correct = row[1] + (1 if is_correct else 0)
    reputation = row[2] + (2 if is_correct else -1)
    if reputation < 0:
        reputation = 0
    if tasks_done >= 50 and tasks_correct / tasks_done >= 0.8:
        level = "🥇 Expert"
    elif tasks_done >= 10 and tasks_correct / tasks_done >= 0.7:
        level = "🥈 Verified"
    else:
        level = "🥉 Beginner"
    actual_reward = reward if is_correct else 0
    c.execute('''UPDATE users SET
        balance = balance + ?,
        tasks_done = ?,
        tasks_correct = ?,
        reputation = ?,
        level = ?
        WHERE telegram_id=?''',
        (actual_reward, tasks_done, tasks_correct, reputation, level, telegram_id)
    )
    conn.commit()
    conn.close()
    return get_user(telegram_id)

def log_task(telegram_id, task_id, is_honeypot, correct_answer, user_answer, reward, tx_hash):
    conn = sqlite3.connect("hivemind.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks_log (telegram_id, task_id, is_honeypot, correct_answer, user_answer, reward, tx_hash) VALUES (?,?,?,?,?,?,?)",
        (telegram_id, task_id, is_honeypot, correct_answer, user_answer, reward, tx_hash)
    )
    conn.commit()
    conn.close()

# =====================
# TASK POOL
# =====================

TASKS_POOL = [
    {
        "id": 101,
        "title": "Identity verification of a project founder",
        "img_url": "https://picsum.photos/id/1025/600/400",
        "context": "Deepfake detection before issuing a 50,000 CSPR grant",
        "reward": 15.0,
        "is_honeypot": False,
        "correct_answer": None
    },
    {
        "id": 102,
        "title": "Geolocation analysis of a node data center",
        "img_url": "https://picsum.photos/id/1043/600/400",
        "context": "Verifying the physical location of a Casper Network validator",
        "reward": 12.0,
        "is_honeypot": False,
        "correct_answer": None
    },
    {
        "id": 103,
        "title": "Document forgery check",
        "img_url": "https://picsum.photos/id/1060/600/400",
        "context": "Verifying a PDF document before signing a smart contract",
        "reward": 18.0,
        "is_honeypot": False,
        "correct_answer": None
    },
    {
        "id": 104,
        "title": "Sentiment classification of a project review",
        "img_url": "https://picsum.photos/id/1074/600/400",
        "context": "Agent is uncertain: positive or negative review about the project",
        "reward": 10.0,
        "is_honeypot": False,
        "correct_answer": None
    },
    {
        "id": 105,
        "title": "Logo plagiarism verification",
        "img_url": "https://picsum.photos/id/1080/600/400",
        "context": "Checking design uniqueness before minting an NFT on Casper",
        "reward": 20.0,
        "is_honeypot": False,
        "correct_answer": None
    },
    {
        "id": 201,
        "title": "Identity verification of a blockchain project advisor",
        "img_url": "https://picsum.photos/id/237/600/400",
        "context": "Verify whether this person's photo appears authentic before approving validator node access.",
        "reward": 10.0,
        "is_honeypot": True,
        "correct_answer": "real"
    },
    {
        "id": 202,
        "title": "Profile photo authenticity check for grant application",
        "img_url": "https://picsum.photos/id/100/600/400",
        "context": "Determine if this profile photo was generated by AI before approving a 30,000 CSPR grant.",
        "reward": 10.0,
        "is_honeypot": True,
        "correct_answer": "fake"
    }
]

def pick_task(tasks_done):
    honeypots = [t for t in TASKS_POOL if t["is_honeypot"]]
    normal = [t for t in TASKS_POOL if not t["is_honeypot"]]
    if tasks_done > 0 and tasks_done % 3 == 0 and honeypots:
        return random.choice(honeypots)
    else:
        return random.choice(normal)

# =====================
# KEYBOARDS
# =====================

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "💰 Earn CSPR"}, {"text": "💼 My Balance"}],
        [{"text": "ℹ️ How it works"}]
    ],
    "resize_keyboard": True,
    "persistent": True
}

NEXT_TASK_KEYBOARD = {
    "inline_keyboard": [[
        {"text": "⚡ Get next task", "callback_data": "next_task"}
    ]]
}

# =====================
# TELEGRAM
# =====================

async def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)

async def send_photo(chat_id: int, photo_url: str, caption: str, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", json=payload)

async def send_task(chat_id: int, user: dict):
    task = pick_task(user["tasks_done"])
    confidence = round(random.uniform(55.0, 68.5), 1)
    reward = task["reward"]
    if user["level"] == "🥇 Expert":
        reward = round(reward * 1.5, 1)

    caption = (
        f"🚨 *REQUEST FROM AI AGENT (Human-in-the-Loop)*\n\n"
        f"🤖 *Agent:* Content Guard v2.6\n"
        f"🎯 *Task:* {task['title']}\n"
        f"📊 *AI Confidence:* `{confidence}%` _(threshold < 70%, human needed)_\n\n"
        f"📝 *Context:* {task['context']}\n\n"
        f"💰 *Reward:* `{reward} CSPR` _(gas paid by agent)_\n"
        f"🏅 *Your level:* {user['level']}"
    )

    honeypot_flag = "1" if task["is_honeypot"] else "0"
    correct = task["correct_answer"] if task["correct_answer"] else "none"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Real photo", "callback_data": f"task_verify_{task['id']}_{reward}_{honeypot_flag}_{correct}_real"},
            {"text": "🤖 AI-Generated", "callback_data": f"task_verify_{task['id']}_{reward}_{honeypot_flag}_{correct}_fake"}
        ]]
    }

    await send_photo(chat_id, task["img_url"], caption, keyboard)

# =====================
# CASPER TRANSACTION
# =====================

async def send_casper_and_notify(chat_id, reward, choice_text, user, task):
    transfer_id = str(random.randint(1, 999999))
    cmd = (
        f'wsl -d Ubuntu /home/casper/.cargo/bin/casper-client transfer '
        f'--node-address https://node.testnet.casper.network '
        f'--amount {int(reward * 1000000000)} '
        f'--secret-key /home/casper/keys/bot_secret_key.pem '
        f'--target-account 020326de467c9de97bac849407c678fe36fd1d4d166b9ca58bd9ccb7abce7ff12a1b '
        f'--chain-name casper-test '
        f'--payment-amount 100000000 '
        f'--transfer-id {transfer_id}'
    )
    try:
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=60, shell=True
        )
        tx_data = json.loads(result.stdout)
        tx_hash = tx_data["result"]["deploy_hash"]
        log_task(chat_id, task["id"], task["is_honeypot"], task["correct_answer"], choice_text, reward, tx_hash)
        level_bonus = "\n⭐ *Expert bonus active!*" if user["level"] == "🥇 Expert" else ""
        new_balance = round(user["balance"] + reward, 2)
        new_rep = user["reputation"] + 2
        await send_message(
            chat_id,
            f"✅ *Answer accepted!*\n\n"
            f"Your choice: *{choice_text}*\n"
            f"💰 Earned: *+{reward} CSPR*\n"
            f"📊 Balance: *{new_balance} CSPR*\n"
            f"🏅 Level: *{user['level']}*\n"
            f"⭐ Reputation: *{new_rep}*{level_bonus}\n\n"
            f"🔗 [View transaction on cspr.live](https://testnet.cspr.live/deploy/{tx_hash})",
            reply_markup=NEXT_TASK_KEYBOARD
        )
    except Exception as e:
        print(f"[CASPER ERROR]: {e}")
        await send_message(
            chat_id,
            "⏳ Transaction is being processed, check your balance later.",
            reply_markup=NEXT_TASK_KEYBOARD
        )

# =====================
# WEBHOOK
# =====================

@app.post("/tg/webhook")
async def tg_webhook(request: Request):
    data = await request.json()

    if "callback_query" in data:
        callback = data["callback_query"]
        callback_data = callback["data"]
        chat_id = callback["message"]["chat"]["id"]

        if callback_data == "next_task":
            user = get_user(chat_id)
            if user:
                await send_task(chat_id, user)
            return {"ok": True}

        parts = callback_data.split("_")
        task_id = int(parts[2])
        reward = float(parts[3])
        is_honeypot = parts[4] == "1"
        correct_answer = parts[5] if parts[5] != "none" else None
        user_choice = parts[6]

        user = get_user(chat_id)
        task = next((t for t in TASKS_POOL if t["id"] == task_id), None)
        choice_text = "✅ Real photo" if user_choice == "real" else "🤖 AI-Generated"

        is_correct = True
        if is_honeypot and correct_answer:
            is_correct = (user_choice == correct_answer)

        update_user_after_task(chat_id, reward, is_correct)

        if not is_correct:
            correct_text = "✅ Real photo" if correct_answer == "real" else "🤖 AI-Generated"
            await send_message(
                chat_id,
                f"❌ *Wrong answer!*\n\n"
                f"This was a control task.\n"
                f"Correct answer: *{correct_text}*\n\n"
                f"⚠️ Reputation decreased. Stay focused!\n"
                f"⭐ Reputation: *{max(0, user['reputation'] - 1)}*",
                reply_markup=NEXT_TASK_KEYBOARD
            )
            return {"ok": True}

        await send_message(chat_id, "⏳ *Sending transaction to Casper Testnet...*")
        asyncio.create_task(send_casper_and_notify(chat_id, reward, choice_text, user, task))
        return {"ok": True}

    if "message" not in data:
        return {"status": "ignored"}

    message = data["message"]
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    username = message["from"].get("username", "unknown")

    if text == "/start":
        user = get_user(chat_id)
        if not user:
            user = create_user(chat_id, username)
            await send_message(
                chat_id,
                f"👋 Welcome to *Casper HiveMind*, @{username}!\n\n"
                f"🤖 AI agents hire humans to complete tasks here.\n"
                f"💰 Earn *CSPR* for every correct answer.\n\n"
                f"🏅 Reputation system:\n"
                f"🥉 Beginner → 🥈 Verified → 🥇 Expert\n\n"
                f"🔐 Your wallet has been created automatically:\n"
                f"`{user['wallet']}`\n\n"
                f"Press *💰 Earn CSPR* to get your first task!",
                reply_markup=MAIN_KEYBOARD
            )
        else:
            await send_message(
                chat_id,
                f"👋 Welcome back, @{username}!",
                reply_markup=MAIN_KEYBOARD
            )
        return {"ok": True}

    elif text == "💰 Earn CSPR":
        user = get_user(chat_id)
        if not user:
            await send_message(chat_id, "Please type /start first")
            return {"ok": True}
        await send_task(chat_id, user)
        return {"ok": True}

    elif text == "💼 My Balance":
        user = get_user(chat_id)
        if user:
            accuracy = 0
            if user["tasks_done"] > 0:
                accuracy = round(user["tasks_correct"] / user["tasks_done"] * 100, 1)
            await send_message(
                chat_id,
                f"💼 *Your Account*\n\n"
                f"👤 @{user['username']}\n"
                f"💰 Balance: *{user['balance']} CSPR*\n"
                f"✅ Tasks completed: *{user['tasks_done']}*\n"
                f"🎯 Accuracy: *{accuracy}%*\n"
                f"⭐ Reputation: *{user['reputation']}*\n"
                f"🏅 Level: *{user['level']}*\n"
                f"🔐 Wallet: `{user['wallet']}`"
            )
        else:
            await send_message(chat_id, "Please type /start first")
        return {"ok": True}

    elif text == "ℹ️ How it works":
        await send_message(
            chat_id,
            f"🤖 *How Casper HiveMind works*\n\n"
            f"1️⃣ An AI agent encounters a task it can't solve with confidence > 70%\n\n"
            f"2️⃣ The agent sends an HTTP 402 Payment Required request with a CSPR budget\n\n"
            f"3️⃣ You receive the task in Telegram and answer with one tap\n\n"
            f"4️⃣ Your answer is verified by our reputation system\n\n"
            f"5️⃣ A real CSPR transaction is fired on Casper Testnet instantly\n\n"
            f"6️⃣ You see the live transaction hash on cspr.live\n\n"
            f"🏅 *Reputation levels:*\n"
            f"🥉 Beginner — basic tasks, standard rewards\n"
            f"🥈 Verified — advanced tasks, better rewards\n"
            f"🥇 Expert — premium tasks, *1.5x reward bonus*\n\n"
            f"⚠️ Control tasks are mixed in randomly to catch cheaters!"
        )
        return {"ok": True}

    else:
        await send_message(
            chat_id,
            "Use the buttons below 👇",
            reply_markup=MAIN_KEYBOARD
        )
        return {"ok": True}
