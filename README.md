# DSA Mentor Agent

DSA Study Mentor Agent — powered by Google ADK & Gemini

Analyzes your LeetCode solve history, identifies weak DSA topics, and generates a personalized daily study plan with curated problems and YouTube video resources.

## Prerequisites

- **uv** — [Install](https://docs.astral.sh/uv/)
- **Gemini API Key** — [Get one free at AI Studio](https://aistudio.google.com/apikey) *(create a new project with no billing enabled for the free tier)*
- **Serper API Key** — [Get one free at serper.dev](https://serper.dev) *(optional — used to find YouTube videos)*

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
| See your weak topics | `What are my weakest DSA topics?` |
| Focus on a specific topic | `I want to practice Dynamic Programming today` |
| Get problems for a topic | `Give me 3 Binary Search problems` |

Generated study plans are saved to:

```
claude-with-leetcode/study_plan/plan_YYYY-MM-DD.md
```

>[!IMPORTANT]
> The study plan is generated based on each user Leetcode history and therefore unique to them. Do not commit your study plan on the submodule 

## How It Works

The agent runs three tools automatically in a single turn:

```
analyze_history()     → Reads .problemSiteData.json, counts problems per topic,
                        flags topics with fewer than 2 problems solved

search_youtube()      → Finds real NeetCode/YouTube videos for each problem
                        via the Serper API

generate_study_plan() → Writes a dated Markdown plan to study_plan/
```

## Troubleshooting

**429 Rate limit error** — You've hit the daily request limit on your free tier. Switch to a model with a higher quota (e.g. `gemini-3.1-flash-lite` has 500 requests/day vs 20 for other models). Update `model` in `app/agent.py`.

**Credits depleted error** — Your API key is linked to a billing-enabled project. Create a new API key at [AI Studio](https://aistudio.google.com/apikey) and attach it to a project with no billing.

**Problem data not found** — Make sure you've initialised the submodule (`git submodule update --init --recursive`) and that `.problemSiteData.json` exists in `claude-with-leetcode/`.