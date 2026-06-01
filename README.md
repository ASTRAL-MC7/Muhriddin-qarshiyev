# @msliderbot — Telegram Bot

## 📁 Files
- `bot.py` — main bot logic
- `database.py` — SQLite database layer
- `requirements.txt` — dependencies
- `Procfile` — Render start command

## 🚀 Deploy to Render

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Set:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

## 🔐 Environment Variables (add in Render dashboard)

| Variable      | Value                                      |
|---------------|--------------------------------------------|
| `BOT_TOKEN`   | Your bot token from @BotFather             |
| `WEBHOOK_URL` | Your Render URL, e.g. `https://your-app.onrender.com` |
| `DB_PATH`     | `bot.db` (or leave default)                |

## ⚙️ BotFather Setup

1. Go to @BotFather → `/setprivacy` → Disable (so bot can read group events)
2. Enable **Join Requests** in channel 2 settings
3. Make sure your bot is **admin** in:
   - `@Milliy_sertifikat_lider` (with "Read messages" permission)
   - Channel 2 (`-1003945305522`) — with **Invite Users** + **Approve join requests** permissions
   - Gift channel (`-1003763206013`) — with **Create invite links** permission

## 📝 Notes

- Render free tier **spins down** after inactivity — upgrade to a paid plan or use a cron ping service (e.g. UptimeRobot) to keep it alive
- SQLite `bot.db` resets on Render redeploy (free tier has no persistent disk). For production, swap `database.py` to PostgreSQL using `DATABASE_URL` env var
