# Live Captions — setup guide

A live transcription app for your iPhone. It listens through the mic and shows
what's being said as large captions. Switch between **Telugu**, **Hindi**, or
**English** (English shows a live translation). Powered by Sarvam AI's Saaras v3.

There are 4 files:

| File | What it is |
|------|-----------|
| `index.html` | The screen you see on your phone |
| `app.py` | The small server ("relay") that holds your key and talks to Sarvam |
| `requirements.txt` | What the server needs to install |
| `manifest.webmanifest` | Makes the home-screen icon launch full-screen |

You don't need a Mac or Xcode. Total time: about 20 minutes, once.

---

## Step 1 — Get a Sarvam API key

1. Go to **dashboard.sarvam.ai** and sign up. New accounts get **₹100 of free credits**
   (about 3+ hours of audio) to try it before paying anything.
2. Create an **API subscription key** and copy it. Keep it private — it's like a password.
3. After free credits, it's **₹30 per hour** of audio — about **₹0.50/minute**, billed by
   the second and only while it's running. (English translation is the same rate. Adding
   speaker labels later would make it ₹45/hour.) Still worth stopping the app when idle.

> Tip: before going further, try Sarvam's free playground on their website and
> speak some real rural Telugu/Hindi at it, to confirm it handles the accents you deal with.

## Step 2 — Put the files online (Render, free)

This makes the app reachable from your phone over HTTPS (the phone mic needs HTTPS).

1. Make a free account at **render.com**.
2. Put these 4 files in a **GitHub** repository (create a repo, upload the files).
3. In Render: **New → Web Service →** connect that repo.
4. Settings:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `python app.py`
5. Open **Environment** and add a variable:
   - Key: `SARVAM_API_KEY`  Value: *(paste your key)*
6. Click **Create Web Service** and wait for it to say "Live". You'll get a URL like
   `https://your-app.onrender.com`.

> The free plan sleeps after idle time, so the first open after a break takes ~30s to wake.

## Step 3 — Use it on your iPhone

1. Open the Render URL in **Safari**.
2. Pick a language, tap **Start**, and allow microphone access.
3. Point the phone toward whoever is speaking.
4. To make it an app: tap **Share → Add to Home Screen**. Now it opens like an app.

---

## Using it in a group / across a room

- Put the phone as close to the speakers as you reasonably can — distance and
  background noise are the hardest case for any transcriber.
- Use the **A+ / A−** buttons to size the text for comfortable reading.
- It captions one person at a time as each finishes a sentence; heavy overlap
  between speakers is where accuracy drops.
- Keep the screen on the app while listening (it tries to stop the screen sleeping).

## Run it on your own PC instead (optional)

```
pip install -r requirements.txt
export SARVAM_API_KEY="your_key_here"     # Windows: set SARVAM_API_KEY=...
python app.py
```

This runs at `http://localhost:8080` on the PC. To reach it from your phone over
HTTPS, expose it with a free tunnel such as **cloudflared** and open the tunnel's
https URL on the phone. (Only works while the PC is on.)

## If something doesn't work

- **"Microphone blocked"** → allow mic for the site in iPhone Settings → Safari.
- **"Could not reach Sarvam — check the API key and credits"** → re-check the
  `SARVAM_API_KEY` value and that your account still has credits.
- **Nothing appears but no error** → make sure you opened the **https** URL, not http.
- **One word/line is wrong** → expected with noisy or far speech; move closer and retry.
