import praw
import csv
import sys
import utils
import re
from datetime import datetime
import os

def get_reddit_posts(config, subreddits, limit, time_filter):
    """Fetches posts from a list of subreddits."""
    print("--- [Reddit] Checking credentials and connecting... ---")
    try:
        reddit = praw.Reddit(
            client_id=config['REDDIT']['CLIENT_ID'],
            client_secret=config['REDDIT']['CLIENT_SECRET'],
            user_agent=config['REDDIT']['USER_AGENT'],
            read_only=True
        )
        reddit.user.me()
        print("--- [Reddit] Connection successful. ---")
    except Exception as e:
        print(f"ERROR: Failed to connect to Reddit. Please check your credentials in config.ini. Error: {e}", file=sys.stderr)
        return []

    all_posts = []
    for subreddit_name in subreddits:
        print(f"--- [Reddit] Fetching top {limit} posts from r/{subreddit_name} for the last {time_filter} ---")
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = subreddit.top(time_filter=time_filter, limit=limit)
            all_posts.extend(list(posts))
        except Exception as e:
            print(f"ERROR: Could not fetch posts from r/{subreddit_name}. Is the name correct? Error: {e}", file=sys.stderr)
    
    print(f"--- [Reddit] Fetched a total of {len(all_posts)} posts. ---")
    return all_posts

def perform_deep_dive(config, problem_posts, context):
    """Performs deep-dive analysis and returns the score and full report text."""
    print("\n--- [Reddit] Starting deep-dive pain point concentration analysis... ---")
    
    post_snippets = []
    for post in problem_posts:
        snippet = f"Title: {post.title}\nBody Snippet: {post.selftext[:400]}"
        post_snippets.append(snippet)

    if not post_snippets:
        print("--- No problem posts to analyze for deep-dive. ---")
        return "N/A", None

    role = f"You are an expert market analyst specializing in the '{context}' domain."
    
    prompt = f'''
{role} Your task is to analyze the following list of user posts to identify recurring pain points.

Here are the posts:
---
{ "---".join(post_snippets) }
---

Please provide a report in Chinese Markdown format with exactly these three sections:

1.  **Top 3-5 Pain Points:** Identify and summarize the most frequently mentioned problems.
2.  **Pain Point Frequency:** Create a Markdown table showing the frequency of each identified pain point.
3.  **Pain Point Concentration Score:** Provide an overall score from 1 (very dispersed) to 10 (highly concentrated) and briefly justify your score.

Finally, on a new line at the very end of your entire response, add the score in the machine-readable format: `Pain-Point-Concentration-Score: X/10` where X is the score.
'''

    gemini_api_key = config['GEMINI']['API_KEY']
    analysis_result = utils.get_gemini_analysis(gemini_api_key, prompt)

    if not analysis_result:
        print("--- [Reddit] Deep-dive analysis failed to produce a result. ---")
        return "N/A", None

    # Extract the score from the result
    concentration_score = "N/A"
    match = re.search(r"Pain-Point-Concentration-Score:\s*(\d+/10)", analysis_result)
    if match:
        concentration_score = match.group(1)
    
    return concentration_score, analysis_result

def run_reddit_analysis(config, subreddits, limit, time_filter, output_file_base, deep_dive=False, context=None, snippet_length=500):
    """Main function to run the Reddit analysis using batch processing."""
    posts = get_reddit_posts(config, subreddits, limit, time_filter)

    if not posts:
        print("--- No posts found. Exiting Reddit analysis. ---")
        return

    print(f"--- Starting batch analysis of {len(posts)} posts with Gemini... ---")
    gemini_api_key = config['GEMINI']['API_KEY']

    posts_for_batch = []
    for i, post in enumerate(posts):
        posts_for_batch.append({
            'id': i,
            'title': post.title,
            'snippet': post.selftext[:snippet_length]
        })

    problem_post_ids = utils.analyze_posts_batch(gemini_api_key, posts_for_batch)

    if problem_post_ids is None:
        print("--- AI analysis failed. No report will be generated. ---")
        return

    problem_posts_count = len(problem_post_ids)
    total_posts = len(posts)
    problem_density = 0
    concentration_score = "N/A"
    
    problem_posts = [posts[i] for i in problem_post_ids]

    # --- Save Problem Density Report (.csv) ---
    output_csv_file = output_file_base + ".csv"
    print(f"--- Found {problem_posts_count} problem posts. Creating output file: {output_csv_file} ---")
    
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['subreddit', 'title', 'url', 'score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for post in problem_posts:
            writer.writerow({
                'subreddit': post.subreddit.display_name,
                'title': post.title,
                'url': post.url,
                'score': post.score
            })
    print(f"List of problem posts saved to {output_csv_file}")

    if total_posts > 0:
        problem_density = (problem_posts_count / total_posts) * 100

    # --- Perform Deep Dive Analysis (if requested) ---
    if deep_dive:
        if not context:
            print("\nWARNING: --deep-dive was specified, but no --context was provided. Deep-dive will be less effective.", file=sys.stderr)
            context = "general products or services"
        
        if problem_posts:
            concentration_score, deep_dive_report_text = perform_deep_dive(config, problem_posts, context)
            
            if deep_dive_report_text:
                # --- Save Deep Dive Report (.md) ---
                summary_header = f"# Deep Dive Analysis for: {context}\n\n"
                summary_header += f"## 📊 Summary Metrics\n"
                summary_header += f"- **Problem Density:** {problem_density:.2f}%\n"
                summary_header += f"- **Pain Point Concentration Score:** {concentration_score}\n\n---\n\n"
                
                full_report = summary_header + deep_dive_report_text
                output_md_file = output_file_base + "_deep_dive.md"
                
                print(f"--- [Reddit] Saving deep-dive analysis report to {output_md_file} ---")
                try:
                    with open(output_md_file, 'w', encoding='utf-8') as f:
                        f.write(full_report)
                    print("--- [Reddit] Report saved successfully. ---")
                except IOError as e:
                    print(f"ERROR: Could not write deep-dive report to file. Error: {e}", file=sys.stderr)
        else:
            print("\n--- No problem posts found, skipping deep-dive analysis. ---")

    # --- Print Final Summary to Console ---
    print("\n---")
    print("📊 Final Summary")
    print("---")
    print(f"- Problem Density: {problem_density:.2f}%")
    print(f"- Pain Point Concentration Score: {concentration_score}")
    print("---")
