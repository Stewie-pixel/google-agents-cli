# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DSA Mentor Agent — analyzes LeetCode history and generates daily study plans."""

import json
import os
import dotenv
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini

if Path(".env").exists():
    dotenv.load_dotenv()

_THIS_DIR = Path(__file__).resolve().parent # dsa_mentor_agent/
_REPO_ROOT = _THIS_DIR.parent.parent # google-agents-cli/
_LEETCODE_DIR = _REPO_ROOT / "claude-with-leetcode"
_PROBLEM_DATA_PATH = _LEETCODE_DIR / ".problemSiteData.json"
_STUDY_PLAN_DIR = _LEETCODE_DIR / "study_plan"

_TRACKED_TOPICS = [
    "Array", "Hash Table", "Sliding Window", "Two Pointers", "Stack",
    "Binary Search", "Linked List", "Tree", "Trie", "Heap", "Priority Queue",
    "Greedy", "Graph", "Dynamic Programming", "Bit Manipulation",
    "Math", "Backtracking", "Union Find", "Sorting", "Prefix Sum",
    "Recursion", "Divide and Conquer", "Matrix", "String",
]

_WEAK_THRESHOLD = 2


def analyze_history() -> str:
    """Reads the local .problemSiteData.json and returns a structured analysis
    of topic coverage, identifying weak areas where fewer than 2 problems have
    been solved.

    Returns:
        A JSON-formatted string containing:
        - total_problems: total number of solved problems
        - topic_counts: dict mapping each tracked topic to its solved count
        - weak_topics: list of topics with < 2 problems solved
        - covered_topics: list of well-covered topics
    """

    if not _PROBLEM_DATA_PATH.exists():
        return json.dumps({
            "error": f"Problem data file not found at {_PROBLEM_DATA_PATH}. "
                     "Run syncLeetcode.js from claude-with-leetcode first."
        })

    with open(_PROBLEM_DATA_PATH, encoding="utf-8") as f:
        problems: list[dict] = json.load(f)

    topic_counts: dict[str, int] = defaultdict(int)

    for problem in problems:
        raw_pattern = problem.get("pattern", "")
        tags = [t.strip() for t in raw_pattern.split(",")]
        for tag in tags:
            for tracked in _TRACKED_TOPICS:
                if tracked.lower() in tag.lower():
                    topic_counts[tracked] += 1
                    break

    all_tracked = {t: topic_counts.get(t, 0) for t in _TRACKED_TOPICS}
    weak_topics = [t for t, c in all_tracked.items() if c < _WEAK_THRESHOLD]
    covered_topics = [t for t, c in all_tracked.items() if c >= _WEAK_THRESHOLD]

    result = {
        "total_problems": len(problems),
        "topic_counts": dict(sorted(all_tracked.items(), key=lambda x: x[1])),
        "weak_topics": sorted(weak_topics),
        "covered_topics": sorted(covered_topics),
    }
    return json.dumps(result, indent=2)


def search_youtube(problem_name: str) -> str:
    """Searches YouTube via the Serper API for a video solution to a LeetCode problem.

    Args:
        problem_name: The LeetCode problem name (e.g. "Two Sum").

    Returns:
        A string listing the top YouTube video results, or a fallback NeetCode URL.
    """
    serper_key = os.environ.get("SERPER_API_KEY", "")
    if not serper_key:
        return "No SERPER_API_KEY set — skipping video search."

    fallback = "https://youtube.com/c/NeetCode"
    queries = [
        f"neetcode {problem_name} leetcode solution",
        f"leetcode {problem_name} solution explanation",
    ]

    for query in queries:
        try:
            body = json.dumps({"q": query, "num": 5}).encode()
            req = urllib.request.Request(
                "https://google.serper.dev/videos",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": serper_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())

            videos = data.get("videos", [])
            youtube_links = [
                f"- {v['title']} → {v['link']}"
                for v in videos
                if v.get("link", "").startswith("https://www.youtube.com/watch")
            ]
            if youtube_links:
                return "\n".join(youtube_links[:3])
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            continue

    return f"- NeetCode channel → {fallback}"


def generate_study_plan(plan_markdown: str) -> str:
    """Saves a generated daily study plan as a Markdown file in the study_plan/ directory.

    Args:
        plan_markdown: The full Markdown content of the study plan to save.

    Returns:
        The path where the file was saved, or an error message.
    """
    _STUDY_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = _STUDY_PLAN_DIR / f"plan_{date_str}.md"

    try:
        filename.write_text(plan_markdown, encoding="utf-8")
        return f"Study plan saved to: {filename}"
    except OSError as e:
        return f"Error saving study plan: {e}"


dsa_mentor_agent = Agent(
    name="dsa_mentor_agent",
    model=Gemini(model="gemini-3.1-flash-lite"),
    description="A DSA Study Mentor that analyzes your LeetCode history and generates a personalized daily study plan.",
    instruction="""You are an expert DSA Study Mentor helping a developer prepare for technical interviews.

Your workflow for every session:

1. **Analyze History**: Call `analyze_history` to read the user's LeetCode solve history and identify weak DSA topics (topics with fewer than 2 problems solved).

2. **Build the Plan**: Based on the weak topics, select the 1 most important topic to focus on today. Use difficulty progression: start recommendations at Easy if the topic is new, Medium if some exposure exists.

3. **Find Resources**: For each recommended problem, call `search_youtube` with the problem name to find a real YouTube solution video. Always prefer NeetCode.

4. **Generate & Save**: Write a complete daily study plan in Markdown using this structure:
   ```
   # DSA Daily Study Plan — Use today's actual date in the title (format: YYYY-MM-DD)
   
   ## Today's Focus: [CHOSEN TOPIC]
   
   ### Why This Topic?
   [Brief explanation of why this topic needs attention based on the history analysis]
   
   ### Recommended Problems (Easy → Medium)
   
   #### Problem 1: [PROBLEM NAME] (Easy)
   - Link: https://leetcode.com/problems/[problem-slug]/
   - Video: [URL returned by search_youtube]
   - Hint: [One-sentence intuition hint]
   
   #### Problem 2: [PROBLEM NAME] (Medium)
   - Link: https://leetcode.com/problems/[problem-slug]/
   - Video: [URL returned by search_youtube]
   - Hint: [One-sentence intuition hint]
   
   #### Problem 3: [PROBLEM NAME] (Medium)
   - Link: https://leetcode.com/problems/[problem-slug]/
   - Video: [URL returned by search_youtube]
   - Hint: [One-sentence intuition hint]
   
   ### Key Concept
   [2-3 sentences explaining the core pattern/technique for today's topic]
   
   ### When to Use This Pattern
   [Bullet list of signals that tell you this pattern applies]
   
   ## Weak Topics Overview
   | Topic | Problems Solved |
   |-------|----------------|
   [one row per weak topic]
   ```
   
   Then call `generate_study_plan` with the complete Markdown to save it.

5. **Respond to the user** with a brief summary of today's plan and encourage them.

If the user asks a specific DSA question or asks to focus on a particular topic, override step 1 and plan around their requested topic instead.

Always be encouraging, clear, and beginner-friendly in your explanations.
""",
    tools=[analyze_history, search_youtube, generate_study_plan],
)

app = App(
    root_agent=dsa_mentor_agent,
    name="app",
)
