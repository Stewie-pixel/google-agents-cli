# dsa-mentor-agent

DSA Study Mentor Agent — powered by Google ADK & Gemini
Agent generated with `agents-cli` version `0.5.0`

---

This agent analyzes your LeetCode solve history from the `claude-with-leetcode` submodule, identifies weak DSA topics, and generates a personalized daily study plan with curated problems and YouTube video resources.

## How It Works

```
analyze_history() ──► Reads .problemSiteData.json
                      Counts problems solved per DSA topic
                      Flags topics with < 2 problems solved

search_youtube()  ──► Calls Serper API to find real NeetCode/YouTube videos
                      for each recommended problem

generate_study_plan() ──► Writes a dated Markdown plan to study_plan/
```

The agent uses **Gemini 2.0 Flash** for reasoning and recommendation generation, and calls all three tools autonomously in a single conversational turn.

## Project Structure

```
dsa-mentor-agent/
├── app/
│   └── agent.py       # Agent definition with 3 tools
├── .env.example       # Environment variable template
└── pyproject.toml     # Project dependencies
```

## Requirements

- **uv**: Python package manager — [Install](https://docs.astral.sh/uv/)
- **agents-cli**: `uv tool install google-agents-cli`
- **Gemini API Key**: [Get one at ai.google.dev](https://ai.google.dev/gemini-api/docs/api-key)
- **Serper API Key**: [Get one at serper.dev](https://serper.dev) (free tier available)

This project also requires the `claude-with-leetcode` submodule to be present at `../claude-with-leetcode` relative to this project (i.e. as a sibling directory in the same repo).

## Quick Start

```bash
# 1. Copy and fill in your environment variables
cp .env.example .env

# 2. Install dependencies
agents-cli install

# 3. Run a query
$env:GEMINI_API_KEY="your-key"
$env:SERPER_API_KEY="your-key"
uv run adk run app "Generate my study plan for today"

# Or ask about a specific topic
uv run adk run app "I want to focus on Dynamic Programming today"
```

## Commands

| Command | Description |
|---|---|
| `agents-cli install` | Install Python dependencies |
| `agents-cli lint` | Run ruff code quality checks |
| `uv run adk run app "<query>"` | Run a single CLI query |
| `uv run adk web app` | Launch the local playground UI |

## Example Queries

```bash
uv run adk run app "Generate my daily study plan"
uv run adk run app "What are my weakest DSA topics?"
uv run adk run app "I want to practice Graphs today"
uv run adk run app "Give me 3 Binary Search problems to solve"
```

## Output

Generated study plans are saved to:
```
../claude-with-leetcode/study_plan/plan_YYYY-MM-DD.md
```

Each plan includes:
- Today's recommended focus topic (based on weakest coverage)
- 2–3 curated LeetCode problems with difficulty progression
- Real YouTube video links (NeetCode preferred)
- One-sentence hints per problem
- Key concept explanation and pattern recognition tips
- Full weak topic overview table
