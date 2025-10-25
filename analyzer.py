import argparse
import configparser
import sys
import os
import re
from datetime import datetime

# Best practice is to structure your project as a package, which avoids sys.path manipulation.
# For now, this works, but consider refactoring if the project grows.
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src import reddit_analyzer
from src import youtube_analyzer
from src import external_analyzer
from src import community_discoverer
from src import keyword_matrix_analyzer

CONFIG_FILE = 'config.ini'

def sanitize_filename(name):
    """Sanitizes a string to be safe for filenames."""
    name = re.sub(r'[\\/*?"<>|]', "", name)
    name = name.replace(' ', '_')
    return name

def get_output_path_base(config, args, command_name, platform):
    """Generates a structured, descriptive base path for output files."""
    base_output_dir = config.get('GENERAL', 'output_dir', fallback='output')
    
    # Call datetime.now() once to ensure consistency
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H%M%S')
    
    structured_dir = os.path.join(base_output_dir, platform, date_str)
    os.makedirs(structured_dir, exist_ok=True)

    subject = ''
    # A concise and extensible way to find the subject from args
    subject_source_map = {
        'keywords': lambda val: '+'.join(val),
        'subreddits': lambda val: '+'.join(val),
        'topic': lambda val: val,
        'channel_id': lambda val: val,
        'channel_url': lambda val: re.search(r'@([\w-]+)', val).group(1) if re.search(r'@([\w-]+)', val) else 'channel'
    }

    for attr, extractor in subject_source_map.items():
        value = getattr(args, attr, None)
        if value:
            subject = sanitize_filename(extractor(value))
            break

    if args.output_file:
        # If a custom output file is given, use it directly within the structured directory
        return os.path.join(structured_dir, sanitize_filename(args.output_file))

    filename_base = f"{command_name}_{subject}_{time_str}" if subject else f"{command_name}_{time_str}"
    return os.path.join(structured_dir, filename_base)

def handle_reddit_command(args, config):
    output_path_base = get_output_path_base(config, args, 'reddit', 'Reddit')
    reddit_analyzer.run_reddit_analysis(
        config=config,
        subreddits=args.subreddits,
        limit=args.limit,
        time_filter=args.time_filter,
        output_file_base=output_path_base,
        deep_dive=args.deep_dive,
        context=args.context
    )

def handle_keyword_matrix_command(args, config):
    output_path_base = get_output_path_base(config, args, 'keyword-matrix', 'YouTube')
    keyword_matrix_analyzer.run_keyword_matrix_analysis(config, args.keywords, output_path_base)

def handle_macro_analysis_command(args, config):
    output_path_base = get_output_path_base(config, args, 'macro', 'YouTube')
    youtube_analyzer.run_macro_analysis(
        config=config,
        channel_url=args.channel_url,
        channel_id=args.channel_id,
        video_limit=args.video_limit,
        sort_by=args.sort_by,
        analyze_trends=args.analyze_trends,
        output_file_base=output_path_base
    )

def handle_micro_analysis_command(args, config):
    output_path_base = get_output_path_base(config, args, 'micro', 'YouTube')
    youtube_analyzer.run_micro_analysis(
        config=config,
        channel_url=args.channel_url,
        channel_id=args.channel_id,
        video_limit=args.video_limit,
        sort_by=args.sort_by,
        comment_limit=args.comment_limit,
        output_file_base=output_path_base
    )

def handle_meso_analysis_command(args, config):
    output_path_base = get_output_path_base(config, args, 'meso', 'YouTube')
    youtube_analyzer.run_meso_analysis(
        config=config,
        channel_url=args.channel_url,
        channel_id=args.channel_id,
        video_limit=args.video_limit,
        sort_by=args.sort_by,
        output_file_base=output_path_base
    )

def handle_discover_communities_command(args, config):
    output_path_base = get_output_path_base(config, args, 'discover', 'Reddit')
    community_discoverer.run_community_discovery(config, args.topic, output_file_base=output_path_base)

def handle_external_analysis_command(args, config):
    output_path_base = get_output_path_base(config, args, 'external', 'YouTube')
    external_analyzer.run_external_analysis(config, args.topic, output_file_base=output_path_base)

def main():
    print("--- Social Listening Toolbox --- \n")
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), CONFIG_FILE)
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)
    config.read(config_path)

    output_dir = config.get('GENERAL', 'output_dir', fallback='output')
    os.makedirs(output_dir, exist_ok=True)

    main_parser = argparse.ArgumentParser(description='A multi-platform tool to analyze community discussions.')
    subparsers = main_parser.add_subparsers(dest='command', help='Available commands')
    # Make subparsers required on Python < 3.7
    subparsers.required = True

    # --- Reddit Parsers ---
    parser_discover = subparsers.add_parser('discover-communities', help='Discover relevant Reddit communities for a given topic.')
    parser_discover.add_argument('topic', type=str, help='The topic or keyword to search for.')
    parser_discover.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')
    parser_discover.set_defaults(func=handle_discover_communities_command)

    parser_reddit = subparsers.add_parser('reddit', help='Analyze Reddit for problem density and optionally perform a deep-dive pain point analysis.')
    parser_reddit.add_argument('subreddits', nargs='+', help='List of subreddits to analyze.')
    parser_reddit.add_argument('--limit', type=int, default=50, help='Number of posts to fetch.')
    parser_reddit.add_argument('--time_filter', type=str, default='month', choices=['all', 'day', 'hour', 'month', 'week', 'year'], help='Time filter for posts.')
    parser_reddit.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')
    parser_reddit.add_argument('--deep-dive', action='store_true', help='If specified, performs a deep-dive pain point concentration analysis on the problem posts.')
    parser_reddit.add_argument('--context', type=str, default=None, help='The topic or context for the deep-dive analysis (e.g., "SaaS pricing"). Required if --deep-dive is used.')
    parser_reddit.set_defaults(func=handle_reddit_command)

    # --- YouTube Parsers ---
    parser_keyword_matrix = subparsers.add_parser('keyword-matrix', help='Analyze and compare multiple YouTube keywords to find opportunities.')
    parser_keyword_matrix.add_argument('keywords', nargs='+', help='A list of keywords to analyze and compare.')
    parser_keyword_matrix.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')
    parser_keyword_matrix.set_defaults(func=handle_keyword_matrix_command)

    parser_external = subparsers.add_parser('external-analysis', help='Analyze a YouTube topic for niche opportunities.')
    parser_external.add_argument('topic', type=str, help='The topic or keyword to search for.')
    parser_external.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')
    parser_external.set_defaults(func=handle_external_analysis_command)

    # --- Parent parser for YouTube channel analysis to avoid repetition (DRY principle) ---
    youtube_channel_parser = argparse.ArgumentParser(add_help=False)
    group_yt = youtube_channel_parser.add_mutually_exclusive_group(required=True)
    group_yt.add_argument('--channel_url', type=str, help='The URL of the YouTube channel.')
    group_yt.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the channel.')
    youtube_channel_parser.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    youtube_channel_parser.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos.')
    youtube_channel_parser.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')

    # --- YouTube Channel Analysis Parsers (using the parent parser) ---
    parser_macro = subparsers.add_parser('macro-analysis', help='Analyze a YouTube channel (Macro level: titles, trends). Low cost.', parents=[youtube_channel_parser])
    parser_macro.add_argument('--analyze_trends', action='store_true', help='Enable content strategy evolution analysis.')
    parser_macro.set_defaults(func=handle_macro_analysis_command)

    parser_meso = subparsers.add_parser('meso-analysis', help='Analyze a YouTube channel (Meso level: thumbnails).', parents=[youtube_channel_parser])
    parser_meso.set_defaults(func=handle_meso_analysis_command)

    parser_micro = subparsers.add_parser('micro-analysis', help='Analyze a YouTube channel (Micro level: comments). High cost.', parents=[youtube_channel_parser])
    parser_micro.add_argument('--comment_limit', type=int, default=15, help='Number of comments to fetch per video.')
    parser_micro.set_defaults(func=handle_micro_analysis_command)

    args = main_parser.parse_args()
    
    # This check is good practice to ensure a function is always called
    if hasattr(args, 'func'):
        args.func(args, config)
    else:
        # If no command is given, print help and exit
        main_parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
