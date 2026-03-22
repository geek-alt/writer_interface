# NovelForge v3.1

AI-powered fanfiction generation. Write complete novels with a local LLM - no cloud, no subscriptions.

## Requirements

| Software | Version | Download |
|---|---|---|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| LM Studio | Latest | https://lmstudio.ai/ |
| VRAM | 8 GB+ | For 8B models (4-bit quantization) |

## Installation

1. Double-click **`install.bat`**
2. Wait for it to finish (~3-5 minutes first time)

## Starting

1. Open **LM Studio** and load a model
   - Recommended: any 7B-13B GGUF, Q4_K_M quantization
   - Click **"Start Server"** (left sidebar -> Local Server -> Start)
2. Double-click **`start.bat`**
3. Browser opens automatically at `http://localhost:8000`

## Getting started

1. In the browser, click **"+ New Project"**
2. Click **"Download blank template"** to get the config file
3. Fill in the template (your MC, fandom, story structure)
4. Upload the filled template
5. Wait for world extraction (~1-2 minutes)
6. Click **"Launch Project"** and start generating!

## FAQ

**LM Studio shows as disconnected (red banner)**
Make sure LM Studio is open, a model is loaded, and the server is running on port 1234.

**Port 8000 is busy**
Another application is using port 8000. Edit `.env` and change `BACKEND_PORT=8001`, then restart.

**Where are my projects stored?**
In the `projects/` folder inside the NovelForge directory. Each project has its own subfolder.

**How do I export my novel?**
In Writer Studio, click the export button (top right) and choose DOCX, EPUB, or PDF.

**The frontend doesn't update after code changes**
Delete `frontend/dist/` and run `start.bat` - it will rebuild automatically.
