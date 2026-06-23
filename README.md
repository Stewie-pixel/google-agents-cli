# DSA Mentor Agent

DSA Study Mentor Agent — powered by Google ADK & Gemini

Analyzes your LeetCode solve history, generates a personalized daily study plan with curated problems and YouTube video resources, and conducts mock technical interviews.

## Demo 

https://github.com/user-attachments/assets/9409429f-79f9-4762-87b1-e90f38512e72

## Prerequisites

- **uv** — [Install](https://docs.astral.sh/uv/)
- **Gemini API Key** — [Get one free at AI Studio](https://aistudio.google.com/apikey) *(create a new project with no billing enabled for the free tier)*
- **Serper API Key** — [Get one free at serper.dev](https://serper.dev) *(required to find YouTube videos)*

## Setup

### 1. Clone the repo with submodules

```bash
git clone --recurse-submodules https://github.com/Stewie-pixel/google-agents-cli.git
cd google-agents-cli/dsa-mentor-agent
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

> [!NOTE]
> The agent always reads API keys from `.env` directly. If you switch to a new API key, just update `.env` — no need to run any terminal commands.

### 3. Install dependencies

```bash
uv sync
```

### 4. Launch the agent

```bash
uv run adk web
```

Then open **http://localhost:8000** in your browser.

## Usage

Once the web UI is open, select **app** from the dropdown and type any of the following:

| What you want | What to type |
|---|---|
| Get today's study plan | `Generate my study plan for today` |
| See your topic coverage | `What are my weakest DSA topics?` |
| Focus on a specific topic | `I want to practice Dynamic Programming today` |
| Get problems for a topic | `Give me 3 Binary Search problems` |
| Start a mock interview | `I want to do a mock interview on Graphs, Medium difficulty` |

Generated study plans are saved to:

```
claude-with-leetcode/study_plan/plan_YYYY-MM-DD.md
```

> [!IMPORTANT]
> The study plan is generated based on your personal LeetCode history and is unique to you. Do not commit your study plans to the submodule.

## How It Works

The agent runs four tools automatically per session:

```
analyze_history()      → Reads .problemSiteData.json, returns full topic and
                         difficulty breakdown tailored to your solve history

search_youtube()       → Finds real NeetCode/YouTube videos for each problem
                         via the Serper API

generate_study_plan()  → Writes a dated Markdown plan to study_plan/

mock_interview()       → Picks a problem from your history or a classic fallback,
                         conducts a back-and-forth interview with follow-up
                         questions, hints, and feedback
```

## Troubleshooting

**429 Rate limit error** — You've hit the daily request limit on your free tier. The recommended model is `gemini-3.1-flash-lite` which has 500 requests/day. Update `model` in `app/agent.py` if needed.

**Credits depleted error** — Your API key is linked to a billing-enabled project. Create a new API key at [AI Studio](https://aistudio.google.com/apikey) attached to a project with no billing enabled.

**Switching API keys not working** — Never set `GEMINI_API_KEY` manually in the terminal. Always update `.env` directly — the agent uses `override=True` when loading env vars so `.env` always takes priority.

**Problem data not found** — Make sure you've initialised the submodule (`git submodule update --init --recursive`) and that `.problemSiteData.json` exists in `claude-with-leetcode/`.
