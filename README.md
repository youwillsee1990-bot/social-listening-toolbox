
# Social Listening Toolbox

A command-line tool to analyze discussions and sentiment on social media platforms like Reddit and YouTube using Google's Gemini AI.

---

## Project Status

*   **Reddit Analyzer**: :white_check_mark: **Functional**. Can fetch posts from subreddits and analyze them for problems/pain points.
*   **YouTube Analyzer**: :white_check_mark: **Functional**. Provides flexible, multi-layered analysis of YouTube channels.
*   **Discover Tool**: :white_check_mark: **Functional**. A powerful tool to find and analyze "blue ocean" niches.

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

### 2. YouTube Channel Analysis

Analyzes videos and comments from a specific YouTube channel, providing both high-level strategic insights and detailed comment analysis.

**Command:**
```bash
python3 analyzer.py youtube --channel_id <UC_CHANNEL_ID> [OPTIONS]
```

**Available Arguments:**
*   `--channel_id` / `--channel_url`: The ID or URL of the channel to analyze.
*   `--video_limit`: Number of videos to analyze (default: 10). How this is applied depends on the `--sort_by` flag.
*   `--sort_by`: Method for selecting videos. (default: `popular`)
    *   `popular`: Analyzes the most-viewed videos. **Note:** This requires fetching the entire video list first and can be slow on large channels.
    *   `newest`: Analyzes the most recently published videos. This is very fast and ideal for quick tests.
*   `--analyze_trends`: A flag to enable in-depth analysis of content strategy evolution. When used, the tool will compare the channel's oldest videos to its newest videos. This requires fetching all videos and will be slow.
*   `--comment_limit`: Number of comments to fetch per video (default: 15).
*   `--output_file`: Name for the output CSV file for comment analysis.

**Examples:**

*   **Quickly analyze the 5 newest videos:**
    ```bash
    python3 analyzer.py youtube --channel_id <UC_CHANNEL_ID> --sort_by newest --video_limit 5
    ```

*   **Deeply analyze the 20 most popular videos:**
    ```bash
    python3 analyzer.py youtube --channel_id <UC_CHANNEL_ID> --sort_by popular --video_limit 20
    ```

*   **Run a full strategy evolution analysis:**
    ```bash
    python3 analyzer.py youtube --channel_id <UC_CHANNEL_ID> --analyze_trends
    ```

**Analysis Features:**

*   **Macro Analysis (Channel-level):**
    *   **Content Strategy:** Identifies main content themes by analyzing video titles.
    *   **Strategy Trend Analysis (via `--analyze_trends`):** Compares the oldest and newest videos to identify shifts in content strategy over time, including time-point estimations.
*   **Micro Analysis (Comment-level):**
    *   **Comment Mining & Classification:** For each comment, the tool fetches its text and like count. It then uses AI to classify the comment into one of the following categories: `Positive Feedback`, `Negative Sentiment`, `Question`, or `Suggestion`.
    *   **Audience Insight:** The results, including the category, a summary, and the like count, are saved to a CSV file. This allows you to easily sort and find popular comments within each category (e.g., find the most-liked `Suggestion`).
    *   **Frequent Question Summary:** After analyzing all comments, the tool automatically aggregates all comments classified as `Question` and generates a final summary of the most frequently asked questions, which is printed to the console.

### 3. Niche Discovery & Analysis

This module helps you find and evaluate "blue ocean" niches by analyzing YouTube search results for a given keyword.

**Command:** `python3 analyzer.py discover --topic "your keyword"`

When run, the tool will perform two key analyses on the top search results:

*   **:ocean: Content Freshness Analysis:**
    *   **What it does:** Checks the publication dates of the top-ranking videos.
    *   **Why it matters:** If the search results are dominated by old videos, it signals a golden opportunity for new content to rank quickly.

*   **:beginner: Channel Authority Analysis:**
    *   **What it does:** Checks the subscriber counts of the channels behind the top-ranking videos.
    *   **Why it matters:** If the results page features many small channels, it proves that the niche is friendly for new creators to compete.

### 4. Future Features (Planned)

*   **:rocket: SEO Recommendations Engine:** An advanced module that provides actionable SEO advice for your own channel based on the analysis of a target channel.

*   **:art: Thumbnail Style Analysis:** A multi-modal analysis feature to understand the visual strategy of thumbnails.
    *   **Style Summary:** For a given channel, analyze the composition, use of text, color schemes, and emotional expression in its thumbnails.
    *   **Style Evolution:** When running trend analysis, compare old and new thumbnails to report on how a channel's visual branding has evolved over time.
