import argparse
import configparser
import sys
import os
import re
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import reddit_analyzer
import youtube_analyzer
import external_analyzer
import community_discoverer
import keyword_matrix_analyzer

CONFIG_FILE = 'config.ini'

def sanitize_filename(name):
    """Sanitizes a string to be safe for filenames."""
    name = re.sub(r'[\\/*?"<>|]', "", name)
    name = name.replace(' ', '_')
    return name

def get_output_path_base(config, args, command_name, platform):
    """Generates a structured, descriptive base path for output files."""
    base_output_dir = config.get('GENERAL', 'output_dir', fallback='output')
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.now().strftime('%H%M%S')
    structured_dir = os.path.join(base_output_dir, platform, date_str)
    os.makedirs(structured_dir, exist_ok=True)

    subject = ''
    if hasattr(args, 'keywords') and args.keywords:
        subject = sanitize_filename('+'.join(args.keywords))
    elif hasattr(args, 'subreddits') and args.subreddits:
        subject = sanitize_filename('+'.join(args.subreddits))
    elif hasattr(args, 'topic') and args.topic:
        subject = sanitize_filename(args.topic)
    elif hasattr(args, 'channel_id') and args.channel_id:
        subject = sanitize_filename(args.channel_id)
    elif hasattr(args, 'channel_url') and args.channel_url:
        match = re.search(r'@([\w-]+)', args.channel_url)
        if match:
            subject = sanitize_filename(match.group(1))
        else:
            subject = 'channel'

    if args.output_file:
        return os.path.join(structured_dir, args.output_file)

    filename_base = f"{command_name}_{subject}_{time_str}"
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
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    main_parser = argparse.ArgumentParser(description='A multi-platform tool to analyze community discussions.')
    subparsers = main_parser.add_subparsers(dest='command', required=True, help='Available commands')

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

    parser_macro = subparsers.add_parser('macro-analysis', help='Analyze a YouTube channel (Macro level: titles, trends). Low cost.')
    group_macro = parser_macro.add_mutually_exclusive_group(required=True)
    group_macro.add_argument('--channel_url', type=str, help='The URL of the YouTube channel.')
    group_macro.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the channel.')
    parser_macro.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    parser_macro.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos.')
    parser_macro.add_argument('--analyze_trends', action='store_true', help='Enable content strategy evolution analysis.')
    parser_macro.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')
    parser_macro.set_defaults(func=handle_macro_analysis_command)

    parser_meso = subparsers.add_parser('meso-analysis', help='Analyze a YouTube channel (Meso level: thumbnails).')
    group_meso = parser_meso.add_mutually_exclusive_group(required=True)
    group_meso.add_argument('--channel_url', type=str, help='The URL of the YouTube channel.')
    group_meso.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the channel.')
    parser_meso.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    parser_meso.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos.')
    parser_meso.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')
    parser_meso.set_defaults(func=handle_meso_analysis_command)

    parser_micro = subparsers.add_parser('micro-analysis', help='Analyze a YouTube channel (Micro level: comments). High cost.')
    group_micro = parser_micro.add_mutually_exclusive_group(required=True)
    group_micro.add_argument('--channel_url', type=str, help='The URL of the YouTube channel.')
    group_micro.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the channel.')
    parser_micro.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    parser_micro.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos.')
    parser_micro.add_argument('--comment_limit', type=int, default=15, help='Number of comments to fetch per video.')
    parser_micro.add_argument('--output_file', type=str, default=None, help='Custom base name for the output file.')
    parser_micro.set_defaults(func=handle_micro_analysis_command)

    args = main_parser.parse_args()
    args.func(args, config)

if __name__ == "__main__":
    main()