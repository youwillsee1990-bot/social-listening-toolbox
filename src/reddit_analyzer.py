import praw
from prawcore.exceptions import PrawcoreException
import csv
import sys
import utils
import re

def _initialize_reddit_client(config):
    """Initializes and authenticates the PRAW client."""
    print("--- [Reddit] Checking credentials and connecting... ---")
    try:
        reddit = praw.Reddit(
            client_id=config['REDDIT']['CLIENT_ID'],
            client_secret=config['REDDIT']['CLIENT_SECRET'],
            user_agent=config['REDDIT']['USER_AGENT'],
            read_only=True,
        )
        reddit.user.me()  # A simple check to verify authentication
        print("--- [Reddit] Connection successful. ---")
        return reddit
    except PrawcoreException as e:
        print(f"ERROR: Failed to connect to Reddit. Please check your credentials in config.ini. Error: {e}", file=sys.stderr)
        return None

def get_reddit_posts(reddit, subreddits, limit, time_filter):
    """Fetches posts from a list of subreddits using an initialized PRAW client."""
    if not reddit:
        return []

    all_posts = []
    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = subreddit.top(time_filter=time_filter, limit=limit)
            all_posts.extend(list(posts))
        except PrawcoreException as e:
            print(f"ERROR: Could not fetch posts from r/{subreddit_name}. Is the name correct? Error: {e}", file=sys.stderr)
    
    print(f"--- [Reddit] Fetched a total of {len(all_posts)} posts. ---")
    return all_posts

def _get_deep_dive_prompt(post_snippets, context):
    """Constructs the prompt for the Gemini deep-dive analysis."""
    role = f"You are an expert market analyst specializing in the '{context}' domain."
    prompt = f'''
{role} Your task is to analyze the following list of user posts to identify recurring pain points.

Here are the posts:
{'-' * 20}
{chr(10).join(post_snippets)}
{'-' * 20}

Based on the posts, provide a detailed analysis including:
1.  **Key Pain Points:** List and describe the most common and significant pain points.
2.  **User Sentiment:** Summarize the overall sentiment (frustration, confusion, desire for solution, etc.).
3.  **Opportunity Areas:** Suggest potential product/service improvements or content ideas based on these pain points.
4.  **Keywords/Phrases:** Identify important keywords or phrases related to the pain points.

Finally, on a new line at the very end of your entire response, add the score in the machine-readable format: `Pain-Point-Concentration-Score: X/10` where X is the score.
'''
    return prompt

def perform_deep_dive(config, problem_posts, context):
    """Performs deep-dive analysis and returns the score and full report text."""
    print("\n--- [Reddit] Starting deep-dive pain point concentration analysis... ---")
    
    post_snippets = [
        f"Title: {post.title}\nBody Snippet: {post.selftext[:400]}"
        for post in problem_posts
    ]

    if not post_snippets:
        print("--- No problem posts to analyze for deep-dive. ---")
        return "N/A", None

    prompt = _get_deep_dive_prompt(post_snippets, context)

    gemini_api_key = config['GEMINI']['API_KEY']
    analysis_result = utils.get_gemini_analysis(gemini_api_key, prompt)
    
    concentration_score_match = re.search(r'Pain-Point-Concentration-Score: (\d+)/10', analysis_result)
    concentration_score = concentration_score_match.group(1) if concentration_score_match else "N/A"
    
    return concentration_score, analysis_result

def _generate_and_save_deep_dive_report(output_file_base, context, problem_density, concentration_score, deep_dive_report_text):
    """Generates the full deep-dive report and saves it to a .md file."""
    summary_header = (
        f"# Deep Dive Analysis for: {context}\n\n"
        f"## 📊 Summary Metrics\n"
        f"- **Problem Density:** {problem_density:.2f}%\n"
        f"- **Pain Point Concentration Score:** {concentration_score}\n\n"
        "---\n\n"
    )
    
    full_report = summary_header + deep_dive_report_text
    output_md_file = output_file_base + "_deep_dive.md"
    
    print(f"--- [Reddit] Saving deep-dive analysis report to {output_md_file} ---")
    try:
        with open(output_md_file, 'w', encoding='utf-8') as f:
            f.write(full_report)
        print("--- [Reddit] Report saved successfully. ---")
    except IOError as e:
        print(f"ERROR: Could not write deep-dive report to file. Error: {e}", file=sys.stderr)

def run_reddit_analysis(config, subreddits, limit, time_filter, output_file_base, deep_dive=False, context=None, snippet_length=500):
    """Main function to run the Reddit analysis using batch processing."""
    reddit_client = _initialize_reddit_client(config)
    posts = get_reddit_posts(reddit_client, subreddits, limit, time_filter)

    if not posts:
        print("--- No posts found. Exiting Reddit analysis. ---")
        return

    # --- Problem Density Analysis ---
    print("\n--- [Reddit] Analyzing problem density... ---")
    problem_posts = []
    for post in posts:
        # Placeholder for actual problem detection logic
        # In a real scenario, this would involve NLP or keyword matching
        if "problem" in post.title.lower() or "issue" in post.selftext.lower():
            problem_posts.append(post)

    problem_density = (len(problem_posts) / len(posts) * 100) if posts else 0
    print(f"--- [Reddit] Problem Density: {problem_density:.2f}% ---")

    # --- Save to CSV ---
    output_csv_file = output_file_base + ".csv"
    print(f"--- [Reddit] Saving analysis results to {output_csv_file} ---")
    try:
        with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['subreddit', 'title', 'score', 'num_comments', 'url', 'is_problematic', 'body_snippet']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for post in posts:
                is_problematic = "problem" in post.title.lower() or "issue" in post.selftext.lower()
                writer.writerow({
                    'subreddit': post.subreddit.display_name,
                    'title': post.title,
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'url': post.url,
                    'is_problematic': is_problematic,
                    'body_snippet': post.selftext[:snippet_length] if post.selftext else ''
                })
        print("--- [Reddit] Analysis results saved successfully. ---")
    except IOError as e:
        print(f"ERROR: Could not write CSV file. Error: {e}", file=sys.stderr)

    # --- Deep Dive Analysis ---
    if deep_dive:
        if not context:
            print("ERROR: --context is required for deep-dive analysis.", file=sys.stderr)
            return
        
        if problem_posts:
            concentration_score, deep_dive_report_text = perform_deep_dive(config, problem_posts, context)
            
            if deep_dive_report_text:
                _generate_and_save_deep_dive_report(output_file_base, context, problem_density, concentration_score, deep_dive_report_text)
        else:
            print("\n--- No problem posts found, skipping deep-dive analysis. ---")

