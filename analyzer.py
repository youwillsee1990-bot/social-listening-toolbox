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

CONFIG_FILE = 'config.ini'

def sanitize_filename(name):
    name = re.sub(r'[\\/*?"<>|]', "", name)
    name = name.replace(' ', '_')
    return name

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), CONFIG_FILE)
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)
    config.read(config_path)

    # Ensure the output directory exists
    output_dir = config.get('GENERAL', 'output_dir', fallback='output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    return config

def get_output_filename_base(config, args, command_name, default_base_prefix):
    output_dir = config.get('GENERAL', 'output_dir', fallback='output')

    if args.output_file:
        return os.path.join(output_dir, args.output_file)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if hasattr(args, 'subreddits') and args.subreddits:
        base_name = sanitize_filename(args.subreddits[0])
        return os.path.join(output_dir, f"{base_name}_{command_name}_{timestamp}")
    
    return os.path.join(output_dir, f"{default_base_prefix}_{timestamp}")

def handle_reddit_command(args, config):
    output_filename_base = get_output_filename_base(config, args, 'reddit', 'reddit_analysis')

    reddit_analyzer.run_reddit_analysis(
        config=config,
        subreddits=args.subreddits,
        limit=args.limit,
        time_filter=args.time_filter,
        output_file_base=output_filename_base,
        deep_dive=args.deep_dive,
        context=args.context
    )

def handle_macro_analysis_command(args, config):
    output_filename_base = get_output_filename_base(config, args, 'macro_analysis', 'macro_analysis')

    youtube_analyzer.run_macro_analysis(
        config=config,
        channel_url=args.channel_url,
        channel_id=args.channel_id,
        video_limit=args.video_limit,
        sort_by=args.sort_by,
        analyze_trends=args.analyze_trends,
        output_file_base=output_filename_base
    )

def handle_micro_analysis_command(args, config):
    output_filename_base = get_output_filename_base(config, args, 'micro_analysis', 'micro_analysis')

    youtube_analyzer.run_micro_analysis(
        config=config,
        channel_url=args.channel_url,
        channel_id=args.channel_id,
        video_limit=args.video_limit,
        sort_by=args.sort_by,
        comment_limit=args.comment_limit,
        output_file_base=output_filename_base
    )

def handle_meso_analysis_command(args, config):
    output_filename_base = get_output_filename_base(config, args, 'meso_analysis', 'meso_analysis')

    youtube_analyzer.run_meso_analysis(
        config=config,
        channel_url=args.channel_url,
        channel_id=args.channel_id,
        video_limit=args.video_limit,
        sort_by=args.sort_by,
        output_file_base=output_filename_base
    )

def handle_discover_communities_command(args, config):
    community_discoverer.run_community_discovery(config, args.topic)

def handle_external_analysis_command(args, config):
    external_analyzer.run_external_analysis(
        config=config,
        topic=args.topic
    )

def main():
    print("--- Social Listening Toolbox --- \n")
    config = load_config()
    
    main_parser = argparse.ArgumentParser(description='A multi-platform tool to analyze community discussions.')
    subparsers = main_parser.add_subparsers(dest='command', required=True, help='Available commands')

    # --- Reddit Parser ---
    parser_reddit = subparsers.add_parser('reddit', help='Analyze Reddit for problem density and optionally perform a deep-dive pain point analysis.')
    parser_reddit.add_argument('subreddits', nargs='+', help='List of subreddits to analyze.')
    parser_reddit.add_argument('--limit', type=int, default=50, help='Number of posts to fetch.')
    parser_reddit.add_argument('--time_filter', type=str, default='month', choices=['all', 'day', 'hour', 'month', 'week', 'year'], help='Time filter for posts.')
    parser_reddit.add_argument('--output_file', type=str, default=None, help='Base name for the output file (e.g., my_analysis). Extension is added automatically.')
    parser_reddit.add_argument('--deep-dive', action='store_true', help='If specified, performs a deep-dive pain point concentration analysis on the problem posts.')
    parser_reddit.add_argument('--context', type=str, default=None, help='The topic or context for the deep-dive analysis (e.g., "SaaS pricing"). Required if --deep-dive is used.')
    parser_reddit.set_defaults(func=handle_reddit_command)

    # --- Macro Analysis Parser (YouTube) ---
    parser_macro = subparsers.add_parser('macro-analysis', help='Analyze a YouTube channel (Macro level: titles, trends). Low cost.')
    group_macro = parser_macro.add_mutually_exclusive_group(required=True)
    group_macro.add_argument('--channel_url', type=str, help='The URL of the YouTube channel.')
    group_macro.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the channel.')
    parser_macro.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    parser_macro.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos.')
    parser_macro.add_argument('--analyze_trends', action='store_true', help='Enable content strategy evolution analysis.')
    parser_macro.add_argument('--output_file', type=str, default=None, help='Base name for the output file (e.g., my_analysis). Extension is added automatically.')
    parser_macro.set_defaults(func=handle_macro_analysis_command)

    # --- Micro Analysis Parser (YouTube) ---
    parser_micro = subparsers.add_parser('micro-analysis', help='Analyze a YouTube channel (Micro level: comments). High cost.')
    group_micro = parser_micro.add_mutually_exclusive_group(required=True)
    group_micro.add_argument('--channel_url', type=str, help='The URL of the YouTube channel.')
    group_micro.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the channel.')
    parser_micro.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    parser_micro.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos.')
    parser_micro.add_argument('--comment_limit', type=int, default=15, help='Number of comments to fetch per video.')
    parser_micro.add_argument('--output_file', type=str, default=None, help='Base name for the output file (e.g., my_analysis). Extension is added automatically.')
    parser_micro.set_defaults(func=handle_micro_analysis_command)

    # --- Meso Analysis Parser (YouTube) ---
    parser_meso = subparsers.add_parser('meso-analysis', help='Analyze a YouTube channel (Meso level: thumbnails).')
    group_meso = parser_meso.add_mutually_exclusive_group(required=True)
    group_meso.add_argument('--channel_url', type=str, help='The URL of the YouTube channel.')
    group_meso.add_argument('--channel_id', type=str, help='The direct ID (UC...) of the channel.')
    parser_meso.add_argument('--video_limit', type=int, default=10, help='Number of videos to analyze.')
    parser_meso.add_argument('--sort_by', type=str, default='popular', choices=['popular', 'newest'], help='Method for selecting videos.')
    parser_meso.add_argument('--output_file', type=str, default=None, help='Base name for the output file.')
    parser_meso.set_defaults(func=handle_meso_analysis_command)

    # --- Community Discovery Parser ---
    parser_discover = subparsers.add_parser('discover-communities', help='Discover relevant Reddit communities for a given topic.')
    parser_discover.add_argument('topic', type=str, help='The topic or keyword to search for.')
    parser_discover.set_defaults(func=handle_discover_communities_command)

    # --- External Analysis Parser ---
    parser_external = subparsers.add_parser('external-analysis', help='Analyze a YouTube topic for niche opportunities.')
    parser_external.add_argument('topic', type=str, help='The topic or keyword to search for.')
    parser_external.set_defaults(func=handle_external_analysis_command)

    args = main_parser.parse_args()
    args.func(args, config)

if __name__ == "__main__":
    main()