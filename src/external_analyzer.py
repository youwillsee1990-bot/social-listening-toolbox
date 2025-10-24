#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module implements the 'external-analysis' feature, which analyzes a YouTube topic
for niche opportunities by evaluating content freshness and channel authority.
"""

import sys
import os
from datetime import datetime, timezone
import utils
from youtube_analyzer import get_youtube_service

def search_videos_by_keyword(youtube_service, topic, max_results=25):
    """Searches for videos on YouTube based on a keyword and returns the top results."""
    print(f"--- Searching YouTube for top {max_results} videos on '{topic}' ---")
    try:
        request = youtube_service.search().list(
            part="snippet",
            q=topic,
            type="video",
            order="relevance",
            maxResults=max_results
        )
        response = request.execute()
        print(f"--- Found {len(response.get('items', []))} videos from search. ---")
        return response.get('items', [])
    except Exception as e:
        print(f"ERROR: Failed to search for videos. Error: {e}", file=sys.stderr)
        return []

def analyze_content_freshness(videos, gemini_api_key):
    """Analyzes video age distribution and returns a markdown summary."""
    print("--- Analyzing Content Freshness ---")
    if not videos:
        return "### Content Freshness Analysis\n\n- No videos to analyze.\n"

    now = datetime.now(timezone.utc)
    age_distribution = {"Under 1 month": 0, "1-6 months": 0, "6-12 months": 0, "Over 1 year": 0}
    
    for video in videos:
        published_at = datetime.fromisoformat(video['snippet']['publishedAt'])
        age_days = (now - published_at).days
        if age_days <= 30: age_distribution["Under 1 month"] += 1
        elif 31 <= age_days <= 180: age_distribution["1-6 months"] += 1
        elif 181 <= age_days <= 365: age_distribution["6-12 months"] += 1
        else: age_distribution["Over 1 year"] += 1

    report = ["### Content Freshness Analysis\n\n**Video Age Distribution:**"]
    for category, count in age_distribution.items():
        report.append(f"- {category}: {count} videos")

    distribution_str = "\n".join([f"{cat}: {count}" for cat, count in age_distribution.items()])
    prompt = f'''As a YouTube niche analyst, evaluate the following distribution of video ages for a search keyword. 
    Based on this data, determine the "Content Freshness" of this niche. 
    A niche with many old videos (over a year) suggests a good opportunity. 
    A niche dominated by very recent videos is highly competitive.

    Data:
    Total videos analyzed: {len(videos)}
    {distribution_str}

    Provide a concise conclusion in Chinese, starting with a "Freshness Score" (e.g., 鲜血指数) from 1-10 (10 being a huge opportunity) and a brief justification.
    '''
    
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        report.append("\n**Summary:**")
        report.append(analysis)
    else:
        report.append("\n**Summary:**\n- AI analysis for content freshness failed.")
    
    return "\n".join(report)

def analyze_channel_authority(youtube_service, videos, gemini_api_key):
    """Analyzes channel subscriber counts and returns a markdown summary."""
    print("--- Analyzing Channel Authority ---")
    if not videos:
        return "### Channel Authority Analysis\n\n- No videos to analyze.\n"

    channel_ids = list(set([video['snippet']['channelId'] for video in videos]))
    report = ["### Channel Authority Analysis"]
    
    try:
        channel_request = youtube_service.channels().list(part="statistics,snippet", id=",".join(channel_ids))
        channel_response = channel_request.execute()
        
        authority_dist = {"< 10k subs": 0, "10k - 100k subs": 0, "100k - 1M subs": 0, "> 1M subs": 0}
        channel_details_map = {item['id']: {'subs': int(item['statistics'].get('subscriberCount', 0)), 'title': item['snippet'].get('title', '[Unknown]')} for item in channel_response.get('items', [])}

        report.append("\n**Ranking Channel Details:**")
        for video in videos:
            ch_id = video['snippet']['channelId']
            info = channel_details_map.get(ch_id, {'subs': 0, 'title': '[Unknown]'}) # Use ch_id here
            report.append(f"- [Subs: {info['subs']:,}] {info['title']} - \"{video['snippet']['title']}\"")

        for video in videos:
            subs = channel_details_map.get(video['snippet']['channelId'], {'subs': 0})['subs']
            if subs < 10000: authority_dist["< 10k subs"] += 1
            elif 10000 <= subs < 100000: authority_dist["10k - 100k subs"] += 1
            elif 100000 <= subs < 1000000: authority_dist["100k - 1M subs"] += 1
            else: authority_dist["> 1M subs"] += 1

        report.append("\n**Video Distribution by Channel Size:**")
        for category, count in authority_dist.items():
            report.append(f"- {category}: {count} videos")

        distribution_str = "\n".join([f"{cat}: {count}" for cat, count in authority_dist.items()])
        prompt = f'''As a YouTube niche analyst, evaluate the following distribution of channel sizes for videos ranking for a keyword.
        Based on this data, determine how "newbie-friendly" the niche is.
        A niche where small channels (<100k subs) can rank is friendly. A niche dominated by huge channels (>1M subs) is very difficult.

        Data:
        Total videos analyzed: {len(videos)}
        {distribution_str}

        Provide a concise conclusion in Chinese, starting with a "Newbie-Friendliness Score" (e.g., 新人友好度) from 1-10 (10 being extremely friendly) and a brief justification.
        '''
        analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
        if analysis:
            report.append("\n**Summary:**")
            report.append(analysis)
        else:
            report.append("\n**Summary:**\n- AI analysis for channel authority failed.")

    except Exception as e:
        report.append(f"\nERROR: Failed to analyze channel authority. Error: {e}")
    
    return "\n".join(report)

def run_external_analysis(config, topic, output_file_base=None):
    """Main function to run the external environment analysis."""
    print(f"--- Initializing External Environment Analysis for topic: '{topic}' ---")

    youtube_service = get_youtube_service(config)
    if not youtube_service:
        print("--- Analysis aborted due to connection failure. ---")
        return

    search_results = search_videos_by_keyword(youtube_service, topic)
    if not search_results:
        print("--- No videos found for this topic. Exiting. ---")
        return

    gemini_api_key = config['GEMINI']['API_KEY']

    freshness_report = analyze_content_freshness(search_results, gemini_api_key)
    authority_report = analyze_channel_authority(youtube_service, search_results, gemini_api_key)

    # Combine reports
    full_report = f"# External Environment Analysis for: {topic}\n\n"
    full_report += f"{freshness_report}\n\n"
    full_report += f"{authority_report}\n"

    # Save the combined report to a file
    if output_file_base:
        output_filename = output_file_base + ".md"
        print(f"\n--- Saving full report to {output_filename} ---")
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(full_report)
            print("--- Report saved successfully. ---")
        except IOError as e:
            print(f"ERROR: Could not write report to file. Error: {e}", file=sys.stderr)

    print("\n--- External Environment Analysis Finished ---")