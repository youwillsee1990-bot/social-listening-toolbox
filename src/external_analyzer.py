#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module implements the 'discover' feature, which analyzes a YouTube topic
for niche opportunities by evaluating content freshness and channel authority.
"""

import sys
from datetime import datetime, timezone

# Assuming utils.py and other modules are in the same src directory
import utils
from youtube_analyzer import get_youtube_service # Re-use the service initializer

def search_videos_by_keyword(youtube_service, topic, max_results=25):
    """Searches for videos on YouTube based on a keyword and returns the top results."""
    print(f"--- Searching YouTube for top {max_results} videos on '{topic}' ---")
    try:
        request = youtube_service.search().list(
            part="snippet",
            q=topic,
            type="video",
            order="relevance", # Order by relevance to simulate a real user search
            maxResults=max_results
        )
        response = request.execute()
        print(f"--- Found {len(response.get('items', []))} videos from search. ---")
        return response.get('items', [])
    except Exception as e:
        print(f"ERROR: Failed to search for videos. Error: {e}", file=sys.stderr)
        return []

def analyze_content_freshness(videos, gemini_api_key):
    """Analyzes the age of a list of videos to determine content freshness."""
    print("\n--- Analyzing Content Freshness ---")
    if not videos:
        print("[-] No videos to analyze.")
        return

    now = datetime.now(timezone.utc)
    age_distribution = {
        "Under 1 month": 0,
        "1-6 months": 0,
        "6-12 months": 0,
        "Over 1 year": 0
    }
    
    for video in videos:
        published_at = datetime.fromisoformat(video['snippet']['publishedAt'])
        age_days = (now - published_at).days

        if age_days <= 30:
            age_distribution["Under 1 month"] += 1
        elif 31 <= age_days <= 180:
            age_distribution["1-6 months"] += 1
        elif 181 <= age_days <= 365:
            age_distribution["6-12 months"] += 1
        else:
            age_distribution["Over 1 year"] += 1

    print("[+] Video Age Distribution:")
    for category, count in age_distribution.items():
        print(f"    - {category}: {count} videos")

    distribution_str = "\n".join([f"{cat}: {count}" for cat, count in age_distribution.items()])
    prompt = f'''As a YouTube niche analyst, evaluate the following distribution of video ages for a search keyword. 
    Based on this data, determine the "Content Freshness" of this niche. 
    A niche with many old videos (over a year) suggests the algorithm is looking for fresh content and represents a good opportunity. 
    A niche dominated by very recent videos is highly competitive.

    Data:
    Total videos analyzed: {len(videos)}
    {distribution_str}

    Provide a concise conclusion in Chinese, starting with a "Freshness Score" (e.g., 鲜血指数) from 1-10 (10 being a huge opportunity for new content) and a brief justification.
    '''
    
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        print("\n[+] Freshness Analysis Summary:")
        print(analysis)
    else:
        print("\n[-] Could not get Freshness Analysis from AI.")

def analyze_channel_authority(youtube_service, videos, gemini_api_key):
    """Analyzes the subscriber counts of channels in a list of videos."""
    print("\n--- Analyzing Channel Authority ---")
    if not videos:
        print("[-] No videos to analyze.")
        return

    channel_ids = list(set([video['snippet']['channelId'] for video in videos]))
    
    try:
        print("[+] Fetching subscriber counts for all channels...")
        channel_request = youtube_service.channels().list(
            part="statistics,snippet", # Also get snippet for channel title
            id=",".join(channel_ids)
        )
        channel_response = channel_request.execute()
        
        authority_distribution = {
            "< 10k subs": 0,
            "10k - 100k subs": 0,
            "100k - 1M subs": 0,
            "> 1M subs": 0
        }

        channel_details_map = {item['id']: {
            'subs': int(item['statistics'].get('subscriberCount', 0)),
            'title': item['snippet'].get('title', '[Unknown Channel]')
        } for item in channel_response.get('items', [])}

        print("\n--- Raw Data for Transparency Test ---")
        print("List of top ranking videos and their channel's subscriber count:")
        for video in videos:
            channel_id = video['snippet']['channelId']
            channel_info = channel_details_map.get(channel_id, {'subs': 0, 'title': '[Unknown]'})
            subs_count = channel_info['subs']
            channel_title = channel_info['title']
            video_title = video['snippet']['title']
            print(f'- [Subs: {subs_count:,}] {channel_title} - "{video_title}"')
        print("-------------------------------------\n")

        for video in videos:
            subs = channel_details_map.get(video['snippet']['channelId'], {'subs': 0})['subs']
            if subs < 10000:
                authority_distribution["< 10k subs"] += 1
            elif 10000 <= subs < 100000:
                authority_distribution["10k - 100k subs"] += 1
            elif 100000 <= subs < 1000000:
                authority_distribution["100k - 1M subs"] += 1
            else:
                authority_distribution["> 1M subs"] += 1

        print("[+] Channel Authority Distribution (by video count):")
        for category, count in authority_distribution.items():
            print(f"    - {category}: {count} videos")

        distribution_str = "\n".join([f"{cat}: {count}" for cat, count in authority_distribution.items()])
        prompt = f'''As a YouTube niche analyst, evaluate the following distribution of channel sizes for videos ranking for a keyword.
        Based on this data, determine the "Channel Authority" dominance and how "newbie-friendly" the niche is.
        A niche where small channels (<100k subs) can rank is friendly. A niche dominated by huge channels (>1M subs) is very difficult for new creators.

        Data:
        Total videos analyzed: {len(videos)}
        {distribution_str}

        Provide a concise conclusion in Chinese, starting with a "Newbie-Friendliness Score" (e.g., 新人友好度) from 1-10 (10 being extremely friendly) and a brief justification.
        '''
        analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
        if analysis:
            print("\n[+] Authority Analysis Summary:")
            print(analysis)
        else:
            print("\n[-] Could not get Authority Analysis from AI.")

    except Exception as e:
        print(f"ERROR: Failed to analyze channel authority. Error: {e}", file=sys.stderr)

def run_external_analysis(config, topic):
    """Main function to run the niche discovery analysis."""
    print(f"--- Initializing Niche Discovery Module for topic: '{topic}' ---")

    youtube_service = get_youtube_service(config)
    if not youtube_service:
        print("--- Niche Discovery aborted due to connection failure. ---")
        return

    search_results = search_videos_by_keyword(youtube_service, topic)
    if not search_results:
        print("--- No videos found for this topic. Exiting. ---")
        return

    gemini_api_key = config['GEMINI']['API_KEY']

    analyze_content_freshness(search_results, gemini_api_key)
    analyze_channel_authority(youtube_service, search_results, gemini_api_key)

    print("\n--- Niche Discovery Module Finished ---")
