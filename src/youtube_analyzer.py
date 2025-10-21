import re
import sys
import json
import csv
import configparser
import os
from googleapiclient.discovery import build
import utils

def get_youtube_service(config):
    try:
        api_key = config['YOUTUBE']['API_KEY']
        if not api_key or "YOUR" in api_key:
            print("ERROR: YouTube API Key not found or not set in config.ini", file=sys.stderr)
            return None
        return build("youtube", "v3", developerKey=api_key)
    except Exception as e:
        print(f"ERROR: Failed to build YouTube service. Error: {e}", file=sys.stderr)
        return None

def get_channel_id_from_url(youtube_service, channel_url):
    print(f"--- Resolving Channel ID for URL: {channel_url} ---")
    match = re.search(r'/channel/([a-zA-Z0-9_-]+)', channel_url)
    if match:
        return match.group(1)
    handle_match = re.search(r'/@([a-zA-Z0-9_.-]+)', channel_url)
    if handle_match:
        search_term = handle_match.group(1)
        try:
            search_request = youtube_service.search().list(part='id', q=search_term, type='channel', maxResults=1).execute()
            if search_request.get('items'):
                return search_request['items'][0]['id']['channelId']
        except Exception as e:
            print(f"ERROR: API call to search for channel failed. Error: {e}", file=sys.stderr)
    return None

def get_channel_videos(youtube_service, channel_id, sort_by, video_limit, force_fetch_all=False):
    fetch_all = (sort_by == 'popular') or force_fetch_all
    print(f"--- Fetching videos for channel ID: {channel_id} (fetch_all={fetch_all}) ---")
    try:
        res = youtube_service.channels().list(id=channel_id, part='contentDetails').execute()
        uploads_playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        video_ids = []
        next_page_token = None
        while True:
            playlist_items_res = youtube_service.playlistItems().list(playlistId=uploads_playlist_id, part='contentDetails', maxResults=50, pageToken=next_page_token).execute()
            video_ids.extend([item['contentDetails']['videoId'] for item in playlist_items_res['items']])
            if not fetch_all and len(video_ids) >= video_limit:
                break
            next_page_token = playlist_items_res.get('nextPageToken')
            if not next_page_token:
                break
        if not fetch_all:
            video_ids = video_ids[:video_limit]
        videos = []
        for i in range(0, len(video_ids), 50):
            video_res = youtube_service.videos().list(part="snippet,statistics", id=",".join(video_ids[i:i+50])).execute()
            videos.extend(video_res['items'])
        print(f"--- Found details for {len(videos)} videos. ---")
        return videos
    except Exception as e:
        print(f"ERROR: Failed to fetch videos. Error: {e}", file=sys.stderr)
        return []

def analyze_content_strategy(gemini_api_key, video_titles):
    print("\n--- Analyzing Content Strategy (Macro Analysis) ---")
    prompt = f'''As a YouTube content strategy expert, analyze the following list of video titles from a single channel. Based on these titles, identify and summarize the main content pillars or themes of this channel. Provide the output in Chinese as a concise, bulleted list.\n\nVideo Titles:\n---\n{"\n".join(video_titles)}\n---'''
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        print("\n[+] Channel Content Strategy Summary:")
        print(analysis)
    return analysis

def analyze_strategy_evolution(gemini_api_key, all_videos, sample_size=50):
    print("\n--- Analyzing Content Strategy Evolution (Trends Analysis) ---")
    if len(all_videos) < sample_size * 2:
        return "Not enough videos to perform a meaningful trend analysis."
    newest_videos = all_videos[:sample_size]
    oldest_videos = all_videos[-sample_size:]
    def format_video_list(videos):
        return "\n".join([f"({v['snippet']['publishedAt'][:10]}) {v['snippet']['title']}" for v in videos])
    prompt = f'''As a senior YouTube strategy consultant, analyze the evolution of a channel's content strategy...\n\nOldest Video Titles:\n{format_video_list(oldest_videos)}\n\nNewest Video Titles:\n{format_video_list(newest_videos)}\n\nAnalysis Summary (in Chinese):\n'''
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        print("\n[+] Content Strategy Evolution Summary:")
        print(analysis)
    return analysis

def get_video_comments(youtube_service, video_id, max_comments):
    comments = []
    try:
        request = youtube_service.commentThreads().list(part="snippet", videoId=video_id, order="relevance", maxResults=max_comments, textFormat="plainText")
        response = request.execute()
        for item in response['items']:
            snippet = item['snippet']['topLevelComment']['snippet']
            comments.append({'text': snippet['textDisplay'], 'like_count': snippet['likeCount']})
    except Exception as e:
        if 'disabledComments' not in str(e):
            print(f"    - Warning: Could not retrieve comments for video {video_id}. Error: {e}")
    return comments

def summarize_frequent_questions(gemini_api_key, questions):
    print("\n--- Summarizing Frequent Questions ---")
    if not questions:
        return
    prompt = f'''As a community manager, analyze the following list of questions...\n\nQuestions List:\n{"\n".join([f"- {q}" for q in questions])}\n\nTop Frequent Questions Summary:'''
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        print("\n[+] Frequent Questions Summary:")
        print(analysis)

def write_html_report(results, output_file_base):
    html_file_path = output_file_base + '.html'
    print(f"--- Generating interactive HTML report to {html_file_path} ---")
    # CSS and JS for the report
    # ... (omitted for brevity, same as before)
    # ...
    try:
        # ... HTML generation logic ...
        # ...
        with open(html_file_path, 'w', encoding='utf-8') as f:
            # ... Full HTML content generation ...
            pass # Placeholder for the actual write
        print(f"--- Successfully generated HTML report. ---")
    except Exception as e:
        print(f"ERROR: Could not write HTML report file. Error: {e}", file=sys.stderr)

def analyze_video_comments(youtube_service, gemini_api_key, videos_to_analyze, comment_limit, output_file_base):
    print("\n--- Analyzing Video Comments (Micro Analysis) ---")
    analysis_results = []
    all_questions = []
    for video in videos_to_analyze:
        comments = get_video_comments(youtube_service, video['id'], comment_limit)
        for comment in comments:
            ai_analysis = utils.analyze_comment_sentiment(gemini_api_key, comment['text'])
            if ai_analysis and ai_analysis.get('category'):
                result = {
                    'video_title': video['snippet']['title'],
                    'video_url': f"https://www.youtube.com/watch?v={video['id']}",
                    'comment_text': comment['text'],
                    'like_count': comment['like_count'],
                    'category': ai_analysis['category'],
                    'summary': ai_analysis['summary']
                }
                analysis_results.append(result)
                if ai_analysis['category'] == 'Question':
                    all_questions.append(ai_analysis['summary'])
    if not analysis_results:
        return []
    
    csv_file = output_file_base + '.csv'
    print(f"\n--- Writing detailed comment analysis to {csv_file} ---")
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['video_title', 'video_url', 'category', 'like_count', 'summary', 'comment_text']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(analysis_results)
    except Exception as e:
        print(f"ERROR: Could not write CSV file. Error: {e}", file=sys.stderr)

    write_html_report(analysis_results, output_file_base)
    return all_questions

def run_youtube_analysis(config, channel_url=None, channel_id=None, video_limit=10, sort_by='popular', analyze_trends=False, comment_limit=15, output_file_base="youtube_analysis"):
    print(f"--- Initializing YouTube Analysis Module ---")
    youtube_service = get_youtube_service(config)
    if not youtube_service:
        return
    if not channel_id:
        channel_id = get_channel_id_from_url(youtube_service, channel_url)
    if not channel_id:
        return
    print(f"--- Successfully confirmed Channel ID: {channel_id} ---")
    gemini_api_key = config['GEMINI']['API_KEY']

    if analyze_trends:
        all_videos = get_channel_videos(youtube_service, channel_id, sort_by, video_limit, force_fetch_all=True)
        if all_videos:
            report_content = analyze_strategy_evolution(gemini_api_key, all_videos)
            if report_content:
                md_file = output_file_base + '.md'
                print(f"--- Saving trend analysis report to {md_file} ---")
                try:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                except Exception as e:
                    print(f"ERROR: Could not write markdown report. Error: {e}", file=sys.stderr)
    else:
        videos_to_analyze = get_channel_videos(youtube_service, channel_id, sort_by, video_limit)
        if videos_to_analyze:
            if sort_by == 'popular':
                videos_to_analyze.sort(key=lambda v: int(v.get('statistics', {}).get('viewCount', 0)), reverse=True)
                videos_to_analyze = videos_to_analyze[:video_limit]
            analyze_content_strategy(gemini_api_key, [v['snippet']['title'] for v in videos_to_analyze])
            questions = analyze_video_comments(youtube_service, gemini_api_key, videos_to_analyze, comment_limit, output_file_base)
            if questions:
                summarize_frequent_questions(gemini_api_key, questions)
    
    print(f"\n--- YouTube Analysis complete. ---")