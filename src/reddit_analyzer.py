import praw
import csv
import sys
import utils

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
        # A quick check to see if credentials are valid
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

def run_reddit_analysis(config, subreddits, limit, time_filter, output_file_base, snippet_length=500):
    """Main function to run the Reddit analysis using batch processing."""
    posts = get_reddit_posts(config, subreddits, limit, time_filter)

    if not posts:
        print("--- No posts found. Exiting Reddit analysis. ---")
        return

    print(f"--- Starting batch analysis of {len(posts)} posts with Gemini... ---")
    gemini_api_key = config['GEMINI']['API_KEY']

    # Prepare posts for batch analysis
    posts_for_batch = []
    for i, post in enumerate(posts):
        posts_for_batch.append({
            'id': i,
            'title': post.title,
            'snippet': post.selftext[:snippet_length]
        })

    # Call the batch analysis function
    problem_post_ids = utils.analyze_posts_batch(gemini_api_key, posts_for_batch)

    if problem_post_ids is None:
        print("--- AI analysis failed. No report will be generated. ---")
        return

    problem_posts_count = len(problem_post_ids)
    total_posts = len(posts)

    # Write the results to a CSV
    output_file = output_file_base + ".csv"
    print(f"--- Found {problem_posts_count} problem posts. Creating output file: {output_file} ---")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        # Note: No 'problem_summary' or 'tags' as we are doing a simple classification
        fieldnames = ['subreddit', 'title', 'url', 'score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, post in enumerate(posts):
            if i in problem_post_ids:
                writer.writerow({
                    'subreddit': post.subreddit.display_name,
                    'title': post.title,
                    'url': post.url,
                    'score': post.score
                })

    print("\n--- Reddit Analysis Complete ---")
    if total_posts > 0:
        problem_density = (problem_posts_count / total_posts) * 100
        print(f"Total posts analyzed: {total_posts}")
        print(f"Problem posts found: {problem_posts_count}")
        print(f"Problem Density: {problem_density:.2f}%")
    else:
        print("No posts were analyzed.")
    print(f"List of problem posts saved to {output_file}")