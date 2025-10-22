
# Social Listening Toolbox

A command-line tool to analyze discussions and sentiment on social media platforms like Reddit and YouTube using Google's Gemini AI.

---

## Project Status

*   **Reddit Analyzer**: :white_check_mark: **Functional**. Can fetch and analyze posts from subreddits.
*   **YouTube Analyzer (Refactored)**: :white_check_mark: **Functional**. The monolithic 'youtube' command has been split into clear, task-oriented commands:
    *   `external-analysis`: Analyzes the competitive environment for a topic.
    *   `macro-analysis`: Analyzes a channel's content strategy (titles, trends).
    *   `micro-analysis`: Analyzes a channel's comment section for audience feedback.
    *   `meso-analysis`: Analyzes a channel's thumbnail visual strategy.

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
    *   Open `config.ini` with a text editor and fill in your keys. 

        *   `[GEMINI] -> API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/app/apikey).
        *   `[REDDIT] -> CLIENT_ID, CLIENT_SECRET, USER_AGENT`: Get from your [Reddit App preferences](https://www.reddit.com/prefs/apps).
        *   `[YOUTUBE] -> API_KEY`: Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials). Ensure the **YouTube Data API v3** is enabled for your project.

--- 

## Usage

The tool is run from the command line using `analyzer.py`.

### 1. Reddit Analysis

Analyzes top posts from one or more subreddits.

**Command:**
```bash
python3 analyzer.py reddit [SUBREDDIT_NAMES...] --limit [NUMBER] --output_file [FILENAME.csv]
```

**Example:**
```bash
python3 analyzer.py reddit OpenAI ChatGPT --limit 50 --output_file reddit_results.csv
```

### 2. External Environment Analysis (YouTube)

Corresponds to the **External Environment** layer of the analysis blueprint. This command helps you find and evaluate "blue ocean" niches by analyzing YouTube search results for a given keyword. (Formerly the `discover` command).

**Command:**
```bash
python3 analyzer.py external-analysis "your_topic"
```

**Analysis Features:**
*   **:ocean: Content Freshness Analysis:** Checks the publication dates of top-ranking videos to see if new content can rank easily.
*   **:beginner: Channel Authority Analysis:** Checks the subscriber counts of ranking channels to see if the niche is friendly to new creators.

**Example:**
```bash
python3 analyzer.py external-analysis "AI Agent Automation"
```

---

### 3. Macro-level Channel Analysis (YouTube)

Corresponds to the **Macro Strategy** layer of the analysis blueprint. This is a **low-cost** command that analyzes a channel's video titles to understand its content strategy and evolution.

**Command:**
```bash
python3 analyzer.py macro-analysis --channel_id <UC_CHANNEL_ID> [OPTIONS]
```

**Available Arguments:**
*   `--channel_id` / `--channel_url`: The ID or URL of the channel to analyze.
*   `--video_limit`: Number of videos to analyze (default: 10).
*   `--sort_by`: `newest` or `popular`. Method for selecting videos.
*   `--analyze_trends`: A flag to enable in-depth analysis of content strategy evolution by comparing the oldest and newest videos.
*   `--output_file`: Base name for the output `.md` report.

**Examples:**

*   **Analyze the 15 newest videos:**
    ```bash
    python3 analyzer.py macro-analysis --channel_id <UC_CHANNEL_ID> --sort_by newest --video_limit 15
    ```

*   **Run a full strategy evolution analysis:**
    ```bash
    python3 analyzer.py macro-analysis --channel_id <UC_CHANNEL_ID> --analyze_trends
    ```

---

### 4. Micro-level Comment Analysis (YouTube)

Corresponds to the **Micro Interaction** layer of the analysis blueprint. This is a **high-cost** command that performs deep analysis on a channel's comment section to understand audience feedback.

**Command:**
```bash
python3 analyzer.py micro-analysis --channel_id <UC_CHANNEL_ID> [OPTIONS]
```

**Available Arguments:**
*   `--channel_id` / `--channel_url`: The ID or URL of the channel to analyze.
*   `--video_limit`: Number of videos to fetch comments from (default: 10).
*   `--sort_by`: `newest` or `popular`. Method for selecting which videos to analyze.
*   `--comment_limit`: Number of comments to fetch per video (default: 15).
*   `--output_file`: Base name for the output `.csv` and `.html` reports.

**Example:**
```bash
# Analyze comments from the 5 most popular videos, 20 comments each
python3 analyzer.py micro-analysis --channel_id <UC_CHANNEL_ID> --sort_by popular --video_limit 5 --comment_limit 20
```
### 5. Future Features (Planned)

*   **:rocket: SEO Recommendations Engine:** An advanced module that provides actionable SEO advice for your own channel based on the analysis of a target channel.
