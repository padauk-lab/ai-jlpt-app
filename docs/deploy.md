# Putting the backend online (free): Render + Neon

Owner: HP (Backend). For the team: everyone uses the same online backend from anywhere, with Expo Go.

| Part | Service | Free plan |
|---|---|---|
| Database | [Neon](https://neon.com) | 0.5 GB, does not expire |
| Backend | [Render](https://render.com) web service (Docker) | 750 hours a month (enough for one service all month), https included |
| Keep awake | [UptimeRobot](https://uptimerobot.com) | Visits `/health` every 5 to 10 minutes, so Render never sleeps |

No credit card is needed for any of them.

## Rules (security)

- **Secrets only go into Render's "Environment" page.** Never into code, commits, chat or screenshots.
- **The online server gets its own new `JWT_SECRET`.** Never reuse the one from your laptop.
- Only HP (backend owner) has the Render and Neon logins.

## 1. Neon (database)

1. Sign up with GitHub. Create a project: name `kyugo`, **Postgres 16**, region **Singapore (AWS ap-southeast-1)**.
2. Copy the **connection string** (starts with `postgresql://`, ends with `sslmode=require`). It is a secret.

## 2. Render (backend)

1. Sign up with GitHub. **New > Web Service**, connect the `padauk-lab/ai-jlpt-app` repository.
2. Settings:
   - **Language:** Docker
   - **Root directory:** `backend`
   - **Branch:** `main` (Render redeploys automatically when main changes)
   - **Region:** Singapore
   - **Instance type:** Free
   - **Health check path:** `/health`
3. **Environment** (each one by hand):

| Name | Value |
|---|---|
| `DATABASE_URL` | the Neon connection string |
| `JWT_SECRET` | a new one: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CLIENT_IP_HEADER` | `cf-connecting-ip` (Cloudflare writes it and refuses fake ones, checked on Oct 27, 2026) |
| `PROXY_HOPS` | `3` (backup only: on Render the list is fake values, user, Cloudflare, Render) |
| `LLM_API_KEY` | the Gemini key (only if the AI buttons should work) |
| `LLM_MODEL` | `gemini-3.8-flash` |
| `AI_EXAMPLES_DAILY_LIMIT` | `50` |
| `EMAIL_MODE` | `log` for now (reset codes appear in Render's log, which only HP can see) |

   `CORS_ORIGINS` stays empty: the phone app doesn't need it.
4. **Create**. The first build takes a few minutes. On every start, the backend sets up the database tables by itself (`alembic upgrade head`).
5. Open `https://<your-service>.onrender.com/health`. It should show `{"status":"ok"}`.

## 3. Load the content (from your computer, once, and after new units)

So the Neon string never lands in your shell history, type it into a hidden prompt:

```
read -s NEON_URL
docker compose run --rm -e DATABASE_URL="$NEON_URL" -v "$PWD/data":/data:ro backend python -m app.content.check_all /data
docker compose run --rm -e DATABASE_URL="$NEON_URL" -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units
unset NEON_URL
```

(After `read -s`, paste the string and press Enter. Nothing is shown, that is on purpose.)

## 4. Keep it awake (UptimeRobot)

1. Sign up, **Add New Monitor**: type **HTTP(s)**, URL `https://<your-service>.onrender.com/health`, interval **5 minutes**.
2. Bonus: it emails you if the backend goes down.

## 5. Check the network limits work

The per-network limits must see each user's own address, not Render's, and a faked address must not help.
From your computer, send 31 wrong logins in a row, each with a different FAKE address and a different email:

```
for i in $(seq 1 31); do curl -s -o /dev/null -w "%{http_code} " -X POST https://<your-service>.onrender.com/api/v1/auth/login -H "Content-Type: application/json" -H "X-Forwarded-For: 10.0.0.$i" -d "{\"email\":\"test$i@example.com\",\"password\":\"wrong-password\"}"; done; echo
```

- Good: the first 30 print `401` and the last one prints `429` (the fake addresses didn't give extra tries).
- Then a teammate on **another network** logs in normally within 5 minutes: it must work (each network has its own limit).
- If all 31 print `401`, or the teammate gets `429`: the backend reads the wrong address. Find the right one:

### Find each user's real address

Only needed if the test above fails again (for example if Render changes its setup). Measured on Oct 27, 2026:
`x-forwarded-for` = (anything the user sent), user, Cloudflare, Render, and `cf-connecting-ip` = user.
A request that sends its own `CF-Connecting-IP` is refused by Cloudflare with 403.

On Render, a request passes Cloudflare, then Render, then our backend. Each proxy can add addresses.

1. In Render's Environment page, add `DEBUG_CLIENT_IP` = `1` and save (Render restarts).
2. Send one test request with fake values:
   ```
   curl -s -o /dev/null -X POST https://<your-service>.onrender.com/api/v1/auth/login -H "Content-Type: application/json" -H "X-Forwarded-For: 6.6.6.6" -d '{"email":"debug@example.com","password":"wrong-password"}'
   ```
3. In Render's Logs, find the line starting with `DEBUG_CLIENT_IP`. Find your own address in it
   (search "what is my IP" in a browser) and see where it is:
   - In `cf-connecting-ip`: set `CLIENT_IP_HEADER` = `cf-connecting-ip`. Best choice.
   - In `x-forwarded-for`: count its place from the END and set `PROXY_HOPS` to that number.
4. **Delete `DEBUG_CLIENT_IP`** (it writes users' addresses to the log), then run the 31-request test again.

## 6. The app

LMHP sets `EXPO_PUBLIC_API_URL=https://<your-service>.onrender.com/api/v1` in `frontend/.env` and opens the app with Expo Go.
