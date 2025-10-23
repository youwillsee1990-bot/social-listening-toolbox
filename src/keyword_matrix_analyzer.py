#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module implements the 'keyword-matrix' feature.
"""

import sys
import os
import json
import statistics
from youtube_analyzer import get_youtube_service
import utils

# --- METRIC CALCULATION CONSTANTS ---
DEMAND_SCORE_CAP_VIEWS = 1000000
COMPETITION_SCORE_CAP_SUBS = 2000000

def analyze_single_keyword(youtube_service, gemini_api_key, keyword):
    """Analyzes a single keyword and returns a dictionary of metrics."""
    print(f"\n--- Analyzing keyword: '{keyword}' ---")
    try:
        print(f"  - Searching for top 10 videos...")
        search_response = youtube_service.search().list(q=keyword, part='id,snippet', maxResults=10, type='video', order='relevance').execute()
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        if not video_ids:
            print("  - No video results found.")
            return None

        print(f"  - Fetching statistics for {len(video_ids)} videos...")
        video_response = youtube_service.videos().list(id=','.join(video_ids), part='statistics,snippet').execute()
        videos = video_response.get('items', [])

        channel_ids = list(set([video['snippet']['channelId'] for video in videos]))
        print(f"  - Fetching statistics for {len(channel_ids)} unique channels...")
        channel_response = youtube_service.channels().list(id=','.join(channel_ids), part='statistics').execute()
        channels = {item['id']: item['statistics'] for item in channel_response.get('items', [])}

        print("  - Calculating scores...")
        view_counts = [int(video.get('statistics', {}).get('viewCount', 0)) for video in videos]
        subscriber_counts = [int(channels.get(video['snippet']['channelId'], {}).get('subscriberCount', 0)) for video in videos]
        avg_views = statistics.mean(view_counts) if view_counts else 0
        avg_subs = statistics.mean(subscriber_counts) if subscriber_counts else 0

        demand_score = min(avg_views / DEMAND_SCORE_CAP_VIEWS, 1.0) * 100
        competition_score = min(avg_subs / COMPETITION_SCORE_CAP_SUBS, 1.0) * 100

        print("  - Getting qualitative analysis from Gemini AI...")
        top_titles = [video['snippet']['title'] for video in videos]
        prompt = f'''
Analyze the YouTube keyword "{keyword}". Top ranking video titles are: {json.dumps(top_titles, indent=2)}

Based on this, provide a JSON object with three keys. The values for these keys MUST be in English:
1.  `matching_keywords`: An array of 5-7 long-tail keywords in English that contain the original keyword.
2.  `related_keywords`: An array of 5-7 semantically related keywords or topics in English that do NOT contain the original keyword.
3.  `questions`: An array of 3-5 common questions in English a user might search for related to this topic.

Your response MUST be a single, valid JSON object.
'''
        qualitative_analysis = utils.get_gemini_analysis(gemini_api_key, prompt, is_json_output=True)

        return {
            "keyword": keyword,
            "demand_score": demand_score,
            "competition_score": competition_score,
            "avg_views": avg_views,
            "avg_subs": avg_subs,
            "top_videos": videos,
            "qualitative_analysis": qualitative_analysis
        }

    except Exception as e:
        print(f"ERROR: Failed to analyze keyword '{keyword}'. Details: {e}", file=sys.stderr)
        return None

def get_opportunity_assessment(gemini_api_key, matrix_data):
    """Gets a final AI assessment for the keyword matrix in bilingual format."""
    print("\n--- Getting final opportunity assessment from Gemini AI... ---")
    prompt = f'''
You are an expert YouTube strategy consultant. Based on the following data matrix, provide a final "Opportunity Assessment" for each keyword.
Your assessment MUST be in the format: "[ICON] [English Assessment] (中文评估)".
Example assessments: "🟢 Golden Opportunity (黄金机会)", "🟡 Worth Trying (值得尝试)", "🔴 Red Ocean (红海市场)".

Data:
{json.dumps(matrix_data, indent=2)}

Return a JSON object where keys are the keywords and values are the bilingual string assessment.
Example: {{"AI agent tutorial": "🔴 Red Ocean (红海市场)"}}
'''
    return utils.get_gemini_analysis(gemini_api_key, prompt, is_json_output=True)

def run_keyword_matrix_analysis(config, keywords, output_file_base):
    """Main function to run the keyword matrix analysis."""
    print(f"--- Initializing Keyword Matrix Analysis for: {keywords} ---")
    youtube_service = get_youtube_service(config)
    gemini_api_key = config['GEMINI']['API_KEY']
    if not youtube_service:
        return

    results = []
    for keyword in keywords:
        result = analyze_single_keyword(youtube_service, gemini_api_key, keyword)
        if result:
            results.append(result)
    
    if not results:
        print("\n--- Keyword Matrix Analysis Finished: No data could be analyzed. ---")
        return

    matrix_for_ai = [{res['keyword']: f"{res['demand_score']:.0f}/100, {res['competition_score']:.0f}/100"} for res in results]
    assessments = get_opportunity_assessment(gemini_api_key, matrix_for_ai)

    print("\n--- Building final report... ---")
    report_parts = [f"# YouTube Keyword Opportunity Matrix\n"]
    
    report_parts.append("## 📊 关键词机会矩阵 (Keyword Opportunity Matrix)\n")
    header = "| 关键词 (Keyword) | 需求热度 (Demand) | 竞争度 (Competition) | 机会评估 (Opportunity) |"
    separator = "|:---|:---:|:---:|:---|"
    report_parts.append(header)
    report_parts.append(separator)
    for res in results:
        keyword = res['keyword']
        assessment = assessments.get(keyword, "N/A") if assessments else "N/A"
        row = f"| {keyword} | {res['demand_score']:.0f}/100 | {res['competition_score']:.0f}/100 | {assessment} |"
        report_parts.append(row)
    
    report_parts.append("\n---\n## 🔍 单个关键词深度分析 (Detailed Keyword Breakdown)\n")
    for res in results:
        report_parts.append(f'### 关键词 (Keyword): "{res["keyword"]}"\n')
        report_parts.append(f"- **需求热度 (Demand Score):** {res['demand_score']:.0f}/100 (基于平均播放量: {res['avg_views']:,.0f})")
        report_parts.append(f"- **竞争度 (Competition Score):** {res['competition_score']:.0f}/100 (基于平均订阅数: {res['avg_subs']:,.0f})")
        
        if res['qualitative_analysis']:
            qa = res['qualitative_analysis']
            report_parts.append("\n**精确匹配词 (Matching Keywords):**")
            report_parts.extend([f"- `{kw}`" for kw in qa.get('matching_keywords', [])])
            report_parts.append("\n**相关主题词 (Related Keywords):**")
            report_parts.extend([f"- `{kw}`" for kw in qa.get('related_keywords', [])])
            report_parts.append("\n**相关问题 (Questions):**")
            report_parts.extend([f"- {q}" for q in qa.get('questions', [])])
        report_parts.append("\n")

    full_report = "\n".join(report_parts)

    # Print summary matrix to console
    print("\n" + "\n".join(report_parts[2:len(results) + 5])) # Adjust slice to show full matrix

    if output_file_base:
        output_filename = output_file_base + ".md"
        print(f"\n--- Saving full report to {output_filename} ---")
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(full_report)
            print("--- Report saved successfully. ---")
        except IOError as e:
            print(f"ERROR: Could not write report to file. Error: {e}", file=sys.stderr)

    print("\n--- Keyword Matrix Analysis Finished ---")
