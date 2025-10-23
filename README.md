# Social Listening Toolbox

A command-line tool to analyze discussions and sentiment on social media platforms like Reddit and YouTube using Google's Gemini AI.

---

## Project Status

*   **Reddit Analyzer**: :white_check_mark: **Functional**. Can discover communities, analyze problem density, and perform deep-dive analysis on pain points.
*   **YouTube Analyzer**: :white_check_mark: **Functional**. A full suite of tools for keyword research, external, macro, meso, and micro analysis.

---

## Setup & Installation

1.  **Clone or download the project files.**

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Keys:**
    *   Create a configuration file by copying the template:
        ```bash
        cp config.template.ini config.ini
        ```
    *   Open `config.ini` with a text editor and fill in your keys for `GEMINI`, `REDDIT`, and `YOUTUBE`.

---

## Usage

The tool is run from the command line using `analyzer.py`. The recommended workflow is to follow the steps in order.

### 1. Community Discovery (Reddit)

**Goal:** Find relevant communities for a broad topic.

This is the first step of your research. Provide a general theme, and the tool will suggest a list of active subreddits to analyze.

**Command:**
```bash
python3 analyzer.py discover-communities "<your_topic>"
```

**Example:**
```bash
python3 analyzer.py discover-communities "AI Agent"
```

---

### 2. Reddit Analysis (Problem & Pain Point)

**Goal:** Analyze the communities from Step 1 to find user problems and summarize pain points.

**Command:**
```bash
python3 analyzer.py reddit [SUBREDDIT_NAMES...] [OPTIONS]
```

**Available Options:**
*   `--limit <NUMBER>`: Number of posts to fetch from each subreddit.
*   `--deep-dive`: Enables the in-depth “Pain Point Concentration” analysis.
*   `--context "<your_topic>"`: Provides a topic for the deep-dive analysis to yield more accurate results.

**Examples:**

*   **Simple Problem Density Analysis:**
    ```bash
    # Use the subreddits found in Step 1
    python3 analyzer.py reddit AIAgent ArtificialInteligence --limit 50
    ```

*   **Full Analysis with Deep-Dive:**
    ```bash
    python3 analyzer.py reddit AIAgent ArtificialInteligence --limit 50 --deep-dive --context "AI Agent Development"
    ```

---

### 3. Keyword Opportunity Matrix (YouTube)

**Goal:** Batch analyze and compare multiple YouTube keywords to find golden opportunities.

This command calculates a "Demand Score" (based on average views) and a "Competition Score" (based on channel authority) for each keyword, then presents them in a comparative matrix.

**Command:**
```bash
python3 analyzer.py keyword-matrix [KEYWORDS...]
```

**Example:**
```bash
python3 analyzer.py keyword-matrix "AI agent tutorial" "SaaS boilerplate" "Next.js starter kit"
```

---

### 4. External Environment Analysis (YouTube)

**Goal:** Deep-dive into a single promising keyword from Step 3 to analyze its competitive environment.

**Command:**
```bash
python3 analyzer.py external-analysis "<your_youtube_topic>"
```

**Example:**
```bash
python3 analyzer.py external-analysis "AI Agent Automation Tutorial"
```

---

### 5. Macro-level Channel Analysis (YouTube)

**Goal:** Analyze a channel’s video titles to understand its content strategy (low-cost).

**Command:**
```bash
python3 analyzer.py macro-analysis --channel_id <UC_CHANNEL_ID> [OPTIONS]
```

---

### 6. Meso-level Visual Analysis (YouTube)

**Goal:** Analyze a channel’s thumbnail images to understand its visual strategy.

**Command:**
```bash
python3 analyzer.py meso-analysis --channel_id <UC_CHANNEL_ID> [OPTIONS]
```

---

### 7. Micro-level Comment Analysis (YouTube)

**Goal:** Analyze a channel’s comment section for audience feedback and sentiment (high-cost).

**Command:**
```bash
python3 analyzer.py micro-analysis --channel_id <UC_CHANNEL_ID> [OPTIONS]
```
