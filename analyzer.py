import argparse
import configparser
import sys
import os

# Add src directory to Python path to allow module imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Now we can import our modules
import reddit_analyzer
import youtube_analyzer
import discover_analyzer

CONFIG_FILE = 'config.ini'

def load_config():
    """Loads API keys and settings from config.ini."""
    config = configparser.ConfigParser()
    # Ensure the script can find the config file, assuming it's in the same directory
    config_path = os.path.join(os.path.dirname(__file__), CONFIG_FILE)
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found in the script directory.")
        print(f"Please copy 'config.template.ini' to '{CONFIG_FILE}' and fill in your API keys.")
        sys.exit(1)
    
    config.read(config_path)
    return config

def handle_reddit_command(args, config):
    """Handler for the 'reddit' command."""
    reddit_analyzer.run_reddit_analysis(
        config=config,
        subreddits=args.subreddits,
        limit=args.limit,
        time_filter=args.time_filter,
        output_file=args.output_file
    )

def handle_youtube_command(args, config):
    """Handler for the 'youtube' command."""
    youtube_analyzer.run_youtube_analysis(
        config=config,
        channel_url=args.channel_url,
        channel_id=args.channel_id,
        video_limit=args.video_limit,
        sort_by=args.sort_by,
        analyze_trends=args.analyze_trends,
        comment_limit=args.comment_limit,
        output_file=args.output_file
    )

def handle_discover_command(args, config):
    """Handler for the 'discover' command."""
    discover_analyzer.run_discover_analysis(
        config=config,
        topic=args.topic
    )


def main():
    """Main entry point for the toolbox."""
    print("--- Social Listening Toolbox --- \n")
    config = load_config()
    
    main_parser = argparse.ArgumentParser(description='A multi-platform tool to analyze community discussions.')
    subparsers = main_parser.add_subparsers(dest='command', required=True, help='Available commands')

    # --- Reddit Parser ---
    parser_reddit = subparsers.add_parser('reddit', help='Analyze Reddit for problem density.')
    parser_reddit.add_argument('subreddits', nargs='+', help='List of subreddits to analyze (e.g., OpenAI ChatGPT).')
    parser_reddit.add_argument('--limit', type=int, default=50, help='Number of posts to fetch from each subreddit.')
    parser_reddit.add_argument('--time_filter', type=str, default='month', choices=['all', 'day', 'hour', 'month', 'week', 'year'], help='Time filter for fetching posts.')
    parser_reddit.add_argument('--output_file', type=str, default='reddit_analysis_results.csv', help='Name of the output CSV file.')
    parser_reddit.set_defaults(func=handle_reddit_command)

    # --- YouTube Parser ---
    parser_youtube = subparsers.add_parser('youtube', help='Analyze a YouTube channel.')
    group = parser_youtube.add_mutually_exclusive_group(required=True)
    group.add_argument('--channel_url', type=str, help='The URL of the YouTube channel to analyze.')
    group.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the YouTube channel.')
    parser_youtube.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    parser_youtube.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos to analyze.')
    parser_youtube.add_argument('--analyze_trends', action='store_true', help='Enable in-depth analysis of content strategy evolution.')
    parser_youtube.add_argument('--comment_limit', type=int, default=15, help='Number of comments to fetch per video (for both top and recent).')
    parser_youtube.add_argument('--output_file', type=str, default='youtube_analysis_results.csv', help='Name of the output CSV file.')
    parser_youtube.set_defaults(func=handle_youtube_command)

    # --- Discover Parser ---
    parser_discover = subparsers.add_parser('discover', help='Analyze a YouTube topic for niche opportunities.')
    parser_discover.add_argument('topic', type=str, help='The topic or keyword to search for (e.g., "AI painting").')
    parser_discover.set_defaults(func=handle_discover_command)

    args = main_parser.parse_args()
    # Call the function associated with the chosen command
    if hasattr(args, 'func'):
        args.func(args, config)
    else:
        main_parser.print_help()

if __name__ == "__main__":
    main()