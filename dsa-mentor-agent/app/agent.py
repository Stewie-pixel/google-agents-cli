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
import random
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
    dotenv.load_dotenv(override=True)

_THIS_DIR = Path(__file__).resolve().parent    # app/
_REPO_ROOT = _THIS_DIR.parent.parent           # google-agents-cli/
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


def analyze_history() -> str:
    """Reads .problemSiteData.json and returns a full snapshot of the user's
    LeetCode history — problems solved per topic, difficulty breakdown, and
    recently solved problems. The agent uses this data to tailor study plans
    and mock interviews to the user's actual history.

    Returns:
        A JSON-formatted string containing:
        - total_problems: total solved problems
        - topic_counts: problems solved per tracked topic (sorted ascending)
        - difficulty_counts: breakdown by Easy / Medium / Hard
        - recent_problems: last 10 solved problems (title, difficulty, topics)
        - all_problems: full list of problems with title, difficulty, and topics
    """
    if not _PROBLEM_DATA_PATH.exists():
        return json.dumps({
            "error": (
                f"Problem data file not found at {_PROBLEM_DATA_PATH}. "
                "Run syncLeetcode.js from claude-with-leetcode first."
            )
        })

    with open(_PROBLEM_DATA_PATH, encoding="utf-8") as f:
        problems: list[dict] = json.load(f)

    topic_counts: dict[str, int] = defaultdict(int)
    difficulty_counts: dict[str, int] = defaultdict(int)
    all_problems = []

    for problem in problems:
        raw_pattern = problem.get("pattern", "")
        difficulty = problem.get("difficulty", "Unknown")
        title = problem.get("title", "Unknown")
        slug = problem.get("titleSlug", "")

        tags = [t.strip() for t in raw_pattern.split(",")]
        matched_topics = []
        for tag in tags:
            for tracked in _TRACKED_TOPICS:
                if tracked.lower() in tag.lower():
                    topic_counts[tracked] += 1
                    matched_topics.append(tracked)
                    break

        difficulty_counts[difficulty] += 1
        all_problems.append({
            "title": title,
            "slug": slug,
            "difficulty": difficulty,
            "topics": matched_topics,
        })

    all_tracked = {t: topic_counts.get(t, 0) for t in _TRACKED_TOPICS}

    result = {
        "total_problems": len(problems),
        "topic_counts": dict(sorted(all_tracked.items(), key=lambda x: x[1])),
        "difficulty_counts": dict(difficulty_counts),
        "recent_problems": all_problems[-10:],
        "all_problems": all_problems,
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


def mock_interview(topic: str, difficulty: str = "Medium") -> str:
    """Picks a LeetCode problem from the user's history matching the given topic
    and difficulty, and returns a mock interview prompt for that problem.
    If no matching solved problem is found, returns a classic problem for that topic.

    Args:
        topic: The DSA topic to interview on (e.g. "Dynamic Programming").
        difficulty: The difficulty level — "Easy", "Medium", or "Hard". Defaults to "Medium".

    Returns:
        A JSON-formatted string containing:
        - problem_title: name of the problem
        - problem_link: LeetCode URL
        - difficulty: difficulty level
        - topic: the topic being tested
        - interview_prompt: the question as a mock interviewer would ask it
        - follow_up_questions: 2-3 follow-up questions to deepen the interview
        - hints: progressive hints to offer if the user gets stuck
        - source: "history" if from solved problems, "classic" if a suggested problem
    """
    if not _PROBLEM_DATA_PATH.exists():
        return json.dumps({"error": "Problem data file not found. Run syncLeetcode.js first."})

    with open(_PROBLEM_DATA_PATH, encoding="utf-8") as f:
        problems: list[dict] = json.load(f)

    # Try to find a matching problem from user's history
    matches = [
        p for p in problems
        if topic.lower() in p.get("pattern", "").lower()
        and p.get("difficulty", "").lower() == difficulty.lower()
    ]

    classic_problems = {
        "Array": ("Two Sum", "two-sum", "Easy"),
        "Dynamic Programming": ("Climbing Stairs", "climbing-stairs", "Easy"),
        "Graph": ("Number of Islands", "number-of-islands", "Medium"),
        "Tree": ("Maximum Depth of Binary Tree", "maximum-depth-of-binary-tree", "Easy"),
        "Linked List": ("Reverse Linked List", "reverse-linked-list", "Easy"),
        "Binary Search": ("Binary Search", "binary-search", "Easy"),
        "Stack": ("Valid Parentheses", "valid-parentheses", "Easy"),
        "Sliding Window": ("Longest Substring Without Repeating Characters", "longest-substring-without-repeating-characters", "Medium"),
        "Two Pointers": ("Valid Palindrome", "valid-palindrome", "Easy"),
        "Hash Table": ("Group Anagrams", "group-anagrams", "Medium"),
        "Heap": ("Kth Largest Element in an Array", "kth-largest-element-in-an-array", "Medium"),
        "Trie": ("Implement Trie (Prefix Tree)", "implement-trie-prefix-tree", "Medium"),
        "Backtracking": ("Subsets", "subsets", "Medium"),
        "Greedy": ("Jump Game", "jump-game", "Medium"),
        "Bit Manipulation": ("Number of 1 Bits", "number-of-1-bits", "Easy"),
        "Math": ("Palindrome Number", "palindrome-number", "Easy"),
        "String": ("Valid Anagram", "valid-anagram", "Easy"),
        "Sorting": ("Sort Colors", "sort-colors", "Medium"),
        "Matrix": ("Spiral Matrix", "spiral-matrix", "Medium"),
        "Recursion": ("Pow(x, n)", "powx-n", "Medium"),
        "Prefix Sum": ("Range Sum Query - Immutable", "range-sum-query-immutable", "Easy"),
        "Divide and Conquer": ("Merge Sort (Merge K Sorted Lists)", "merge-k-sorted-lists", "Hard"),
        "Union Find": ("Number of Connected Components in an Undirected Graph", "number-of-connected-components-in-an-undirected-graph", "Medium"),
    }

    if matches:
        chosen = random.choice(matches)
        title = chosen.get("title", "Unknown")
        slug = chosen.get("titleSlug", title.lower().replace(" ", "-"))
        source = "history"
    else:
        fallback = classic_problems.get(topic, ("Two Sum", "two-sum", "Easy"))
        title, slug, difficulty = fallback
        source = "classic"

    result = {
        "problem_title": title,
        "problem_link": f"https://leetcode.com/problems/{slug}/",
        "difficulty": difficulty,
        "topic": topic,
        "source": source,
        "interview_prompt": (
            f"Let's do a mock interview! I'll be your interviewer today.\n\n"
            f"**Problem: {title}** ({difficulty})\n"
            f"Link: https://leetcode.com/problems/{slug}/\n\n"
            f"Take a moment to read the problem. When you're ready, walk me through "
            f"your thought process before writing any code. I want to hear:\n"
            f"1. How you understand the problem\n"
            f"2. Any edge cases you can think of\n"
            f"3. Your initial approach and its time/space complexity\n\n"
            f"Take your time — there's no rush."
        ),
        "follow_up_questions": [
            f"What is the time and space complexity of your solution?",
            f"Can you think of a more optimal approach?",
            f"How would your solution handle edge cases like an empty input or very large values?",
        ],
        "hints": [
            "Think about what data structure would make lookups O(1).",
            "Consider whether sorting the input first simplifies the problem.",
            "Try working through a small example by hand before coding.",
        ],
    }
    return json.dumps(result, indent=2)


dsa_mentor_agent = Agent(
    name="dsa_mentor_agent",
    model=Gemini(model="gemini-3.1-flash-lite"),
    description="A DSA Study Mentor that analyzes your LeetCode history, generates personalized daily study plans, and conducts mock interviews.",
    instruction="""You are an expert DSA Study Mentor helping a developer prepare for technical interviews.

You have access to four tools: `analyze_history`, `search_youtube`, `generate_study_plan`, and `mock_interview`.

## Workflow 1: Generate a Study Plan

When the user asks for a study plan:

1. **Analyze History**: Call `analyze_history` to get the user's full LeetCode history — topic counts, difficulty breakdown, and recent problems.

2. **Tailor the Plan**: Use the data to understand what the user needs:
   - If they have gaps (topics with 0–1 problems), prioritize those
   - If they've been solving only Easy problems, push toward Medium
   - If they recently solved problems in a topic, build on that momentum
   - Always match recommendations to their actual skill level from the data

3. **Find Resources**: For each recommended problem, call `search_youtube` to find a real YouTube solution video. Always prefer NeetCode.

4. **Generate & Save**: Write a complete daily study plan in Markdown using this structure:

   ```
   # DSA Daily Study Plan — [TODAY'S DATE in YYYY-MM-DD format]

   ## Today's Focus: [CHOSEN TOPIC]

   ### Why This Topic?
   [Explanation tied to the user's actual history data]

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
   [2-3 sentences explaining the core pattern/technique]

   ### When to Use This Pattern
   [Bullet list of signals that tell you this pattern applies]

   ## Topic Overview
   | Topic | Problems Solved |
   |-------|----------------|
   [one row per topic, sorted by count ascending]
   ```

   Then call `generate_study_plan` with the complete Markdown to save it.

5. **Respond** with a brief summary of today's plan and encourage the user.

## Workflow 2: Mock Interview

When the user asks for a mock interview or wants to practice a specific topic:

1. Ask them which topic and difficulty they want to practice (if not already specified).
2. Call `mock_interview` with the topic and difficulty.
3. Present the `interview_prompt` from the result naturally, as a real interviewer would.
4. Wait for the user's response.
5. Engage in a back-and-forth interview:
   - Ask the `follow_up_questions` one at a time based on their answers
   - Offer `hints` progressively only if the user is stuck
   - Give constructive feedback on their approach
   - At the end, summarize their performance and suggest what to review

## General Rules

- Always base recommendations on the user's actual history data, not generic advice
- Be encouraging, clear, and beginner-friendly
- If the user asks a specific DSA question, answer it directly without running the full workflow
- If the user wants to focus on a specific topic, skip the history analysis and build the plan around their request
""",
    tools=[analyze_history, search_youtube, generate_study_plan, mock_interview],
)

app = App(
    root_agent=dsa_mentor_agent,
    name="app",
)