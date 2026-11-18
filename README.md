# <img src="icon.png" width="40" valign="middle"> PrepDrop

Stop manually sorting your prep materials. Paste a link, note, or resource — the app figures out where it belongs in your folder and puts it there.

## What it does

You paste anything into the text box:
- A link: `https://arxiv.org/abs/...`
- A note: `"At the Meta screen they asked about two-tower rec sys models"`
- A book tip: `"Sutton & Barto ch.13 covers policy gradients clearly"`
- A reminder: `"For Anthropic: re-read the RLHF paper before the loop"`

The app reads your folder structure, decides the best location, and writes or appends to the right file — showing you exactly what it did.

## Setup

### 1. Get an API key

PrepDrop works with either **Anthropic** or **OpenAI** — use whichever you already have.

- **Anthropic:** [console.anthropic.com](https://console.anthropic.com) — keys start with `sk-ant-`
- **OpenAI:** [platform.openai.com](https://platform.openai.com) — keys start with `sk-`

The free tier of either is enough to get started.

### 2. Set up your notes folder
Organize it however you like — by company, by topic, or both. Example:

```
prep-notes/
  Meta/
  Google/
  Anthropic/
  topics/
    systems-design/
    ML-fundamentals/
    RL/
```

### 3. Run locally (recommended)

Running locally means PrepDrop can access any folder on your machine — no cloud sync required.

```bash
git clone https://github.com/amirreisizadeh/prepdrop
cd prepdrop
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."   # or OPENAI_API_KEY="sk-..."
export NOTES_ROOT="/path/to/your/notes"
streamlit run app.py
```

On macOS you can double-click `launch.command` after the first setup instead of typing these commands each time.

### 4. Use the hosted app (alternative)

If you don't want to run anything locally, open the hosted version instead:

**[prepdrop.streamlit.app →](https://prepdrop.streamlit.app)**

No installation needed — just bring your API key. The one limitation: your notes folder must be cloud-synced (Dropbox, Google Drive, or iCloud Drive) so the app can reach it. Enter the full path in the sidebar, e.g. `/Users/yourname/Dropbox/prep-notes`.

## Tips

- **Add context to links** — `https://x.com/... — good explanation of KV cache for systems design` will be filed more precisely than a bare URL
- **The more organized your folder**, the better the app places things — it reads your existing structure to decide
- **Word files are supported** — the app can read and append to `.docx` files as well as plain text and Markdown

## Cost

Each resource costs roughly $0.01–0.03 in API usage depending on how much the model needs to explore your folder. With a $5 credit you can organize hundreds of resources.
