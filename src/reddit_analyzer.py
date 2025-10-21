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

def run_reddit_analysis(config, subreddits, limit, time_filter, output_file_base):
    """Main function to run the Reddit analysis."""
    posts = get_reddit_posts(config, subreddits, limit, time_filter)

    if not posts:
        print("--- No posts found. Exiting Reddit analysis. ---")
        return

    output_file = output_file_base + ".csv"
    print(f"--- Creating output file: {output_file} ---")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['subreddit', 'title', 'url', 'score', 'is_problem_post', 'problem_summary', 'tags']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        total_posts = len(posts)
        problem_posts_count = 0
        print(f"--- Starting analysis of {total_posts} posts with Gemini... ---")

        gemini_api_key = config['GEMINI']['API_KEY']

        for i, post in enumerate(posts):
            print(f"Analyzing post {i+1}/{total_posts}: \"{post.title[:50]}...\"")
            # Use the utility function for analysis
            ai_analysis = utils.analyze_post_with_gemini(gemini_api_key, post.title, post.selftext)

            if ai_analysis and ai_analysis.get('is_problem_post'):
                problem_posts_count += 1
                writer.writerow({
                    'subreddit': post.subreddit.display_name,
                    'title': post.title,
                    'url': post.url,
                    'score': post.score,
                    'is_problem_post': True,
                    'problem_summary': ai_analysis.get('problem_summary'),
                    'tags': ', '.join(ai_analysis.get('tags', []))
                })

    print("\n--- Reddit Analysis Complete ---")
    if total_posts > 0:
        problem_density = (problem_posts_count / total_posts) * 100
        print(f"Total posts analyzed: {total_posts}")
        print(f"Problem posts found: {problem_posts_count}")
        print(f"Problem Density: {problem_density:.2f}%")
    else:
        print("No posts were analyzed.")
    print(f"Results saved to {output_file}")