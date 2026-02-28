# DEPLOY_RENDER.md — Midolli-AI Deployment Guide (Render.com)

## Prerequisites
- Render.com account (free tier sufficient)
- GitHub repo: `https://github.com/R-midolli/Midolli-AI`
- 3 API keys: `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, `NVIDIA_API_KEY`

---

## Step 1 — Create a New Web Service on Render

1. Go to https://dashboard.render.com
2. Click **New** → **Web Service**
3. **Connect repository** → authorize GitHub → select `Midolli-AI`
4. Click **Connect**

---

## Step 2 — Configure the Service

| Field | Value |
|-------|-------|
| **Name** | `midolli-ai` |
| **Region** | `Frankfurt (EU Central)` |
| **Branch** | `master` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python backend/ingest.py` |
| **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

---

## Step 3 — Set Environment Variables

In **Environment → Environment Variables**, add exactly these 3 keys:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY_1` | Your first Gemini API key |
| `GEMINI_API_KEY_2` | Your second Gemini API key |
| `NVIDIA_API_KEY` | Your NVIDIA API key |

Click **Save Changes**.

---

## Step 4 — Deploy

Click **Deploy Web Service**. Wait ~3-5 minutes for the build to complete.

Once deployed, your URL will be: `https://midolli-ai.onrender.com`

Verify with: `curl https://midolli-ai.onrender.com/health`
Expected: `{"status":"ok","service":"Midolli-AI"}`

---

## Step 5 — Update Portfolio API URL

In `portfolio_rafael_midolli/index.html`, replace the placeholder URL in the snippet near the bottom of the file:

```html
apiUrl: 'https://midolli-ai.onrender.com',
```

> **Note:** If your Render service gets a different URL (e.g., `midolli-ai-abc.onrender.com`), update this line accordingly.

Then commit and push:
```bash
cd C:\Users\rafae\workspace\portfolio_rafael_midolli
git add index.html
git commit -m "fix: update Midolli-AI API URL to Render endpoint"
git push
```

---

## Step 6 — Anti-Sleep with UptimeRobot (Free)

Render's free tier sleeps after 15 minutes of inactivity. Prevent this with UptimeRobot:

1. Go to https://uptimerobot.com → Sign up (free)
2. Click **Add New Monitor**
3. Configure:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `Midolli-AI Health`
   - **URL**: `https://midolli-ai.onrender.com/health`
   - **Monitoring Interval**: `5 minutes`
4. Click **Create Monitor**

This sends a ping every 5 minutes, preventing Render from spinning down the service.

---

## Step 7 — Verify Everything

```bash
# Health check
curl https://midolli-ai.onrender.com/health
# Expected: {"status":"ok","service":"Midolli-AI"}

# Test chat
curl -X POST https://midolli-ai.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quels sont les projets de Rafael ?","history":[]}'
# Expected: {"reply":"...","sources":[...],"api_used":"..."}
```

Then visit `https://r-midolli.github.io/portfolio_rafael_midolli/` and confirm the violet FAB (floating chat button) is visible in the bottom-right corner.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `/health` returns 500 | Missing env vars | Check Render → Environment tab |
| Widget shows "error" | CORS issue | Verify portfolio URL in `main.py` CORS origins |
| Bot replies "I don't know" | Ingest failed | Check Render build logs for ingest errors |
| Slow first response | Free tier cold start | Configure UptimeRobot (Step 6) |
