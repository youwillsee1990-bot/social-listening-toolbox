#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module implements the 'discover-communities' feature, which suggests
relevant subreddits for a given topic.
"""

import sys
import praw

def find_subreddits(config, topic, limit=10):
    """
    Searches for subreddits related to a topic using the Reddit API and returns a ranked list.
    """
    print(f"--- Connecting to Reddit to search for subreddits related to: '{topic}' ---")
    try:
        reddit = praw.Reddit(
            client_id=config['REDDIT']['CLIENT_ID'],
            client_secret=config['REDDIT']['CLIENT_SECRET'],
            user_agent=config['REDDIT']['USER_AGENT'],
            read_only=True
        )
        reddit.user.me() # A quick check to see if credentials are valid
    except Exception as e:
        print(f"ERROR: Failed to connect to Reddit. Please check your API credentials in config.ini. Details: {e}", file=sys.stderr)
        return []

    found_subreddits = []
    try:
        print(f"--- Searching for subreddits matching '{topic}'... ---")
        # Search for subreddits, fetch more to filter
        for subreddit in reddit.subreddits.search(topic, limit=limit*2): 
            # Basic filter to ensure relevance
            if topic.lower() in subreddit.display_name.lower() or topic.lower() in str(subreddit.public_description).lower():
                 found_subreddits.append({
                     'name': subreddit.display_name_prefixed,
                     'subscribers': subreddit.subscribers
                 })

        if not found_subreddits:
            print("--- No relevant subreddits found. ---")
            return []
        
        # Sort by subscribers and take the top 'limit'
        sorted_subreddits = sorted(found_subreddits, key=lambda x: x['subscribers'], reverse=True)[:limit]
        
        print(f"--- Found and filtered {len(sorted_subreddits)} relevant subreddits. ---")
        return sorted_subreddits

    except Exception as e:
        print(f"ERROR: An error occurred while searching for subreddits. Details: {e}", file=sys.stderr)
        return []

def run_community_discovery(config, topic):
    """Main function to run the community discovery analysis."""
    print(f"--- Initializing Community Discovery Module for topic: '{topic}' ---")
    
    found_subreddits = find_subreddits(config, topic)
    
    print("\n[+] Recommended subreddits to analyze:")
    # Sort by subscribers, descending
    for sub in sorted(found_subreddits, key=lambda x: x['subscribers'], reverse=True):
        print(f"- {sub['name']} (Subscribers: {sub['subscribers']:,})")
        
    print("\n--- Community Discovery Module Finished ---")
