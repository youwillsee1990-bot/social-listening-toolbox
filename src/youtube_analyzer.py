import re
import sys
import json
import csv
import configparser
from googleapiclient.discovery import build
import utils # Import the shared utility module

def get_youtube_service(config):
    """Builds and returns a YouTube API service object."""
    try:
        api_key = config['YOUTUBE']['API_KEY']
        if not api_key or "YOUR" in api_key:
            print("ERROR: YouTube API Key not found or not set in config.ini under [YOUTUBE] section.", file=sys.stderr)
            return None
        
        api_service_name = "youtube"
        api_version = "v3"
        
        print("--- Building YouTube API service... ---")
        youtube_service = build(api_service_name, api_version, developerKey=api_key)
        print("--- Successfully built YouTube API service. ---")
        return youtube_service

    except Exception as e:
        print(f"ERROR: Failed to build YouTube service. Check API Key and ensure YouTube Data API v3 is enabled. Error: {e}", file=sys.stderr)
        return None

def get_channel_id_from_url(youtube_service, channel_url):
    """Extracts the channel ID from various YouTube URL formats."""
    print(f"--- Resolving Channel ID for URL: {channel_url} ---")
    
    match = re.search(r'/channel/([a-zA-Z0-9_-]+)', channel_url)
    if match:
        return match.group(1)

    handle_match = re.search(r'/@([a-zA-Z0-9_.-]+)', channel_url)
    user_match = re.search(r'/user/([a-zA-Z0-9_.-]+)', channel_url)
    
    search_term = None
    if handle_match:
        search_term = handle_match.group(1)
    elif user_match:
        search_term = user_match.group(1)

    if search_term:
        print(f"--- Found handle/username: {search_term}. Searching for Channel ID via API... ---")
        try:
            search_request = youtube_service.search().list(part='id', q=search_term, type='channel', maxResults=1).execute()
            if search_request.get('items'):
                return search_request['items'][0]['id']['channelId']
            else:
                print(f"ERROR: Could not find a channel for handle/username: {search_term}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"ERROR: API call to search for channel failed. Error: {e}", file=sys.stderr)
            return None
    
    print(f"ERROR: Could not parse a known format from the URL: {channel_url}", file=sys.stderr)
    return None

def get_channel_videos(youtube_service, channel_id, sort_by, video_limit, force_fetch_all=False):
    fetch_all = (sort_by == 'popular') or force_fetch_all
    if fetch_all:
        print(f"--- Fetching ALL videos for channel ID: {channel_id} for '{sort_by}' analysis. This may be slow. ---")
    else:
        print(f"--- Fetching {video_limit} newest videos for channel ID: {channel_id}. ---")

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
            video_chunk_ids = ",".join(video_ids[i:i+50])
            video_res = youtube_service.videos().list(part="snippet,statistics", id=video_chunk_ids).execute()
            videos.extend(video_res['items'])

        print(f"--- Found details for {len(videos)} videos. ---")
        return videos
    except Exception as e:
        print(f"ERROR: Failed to fetch videos for channel {channel_id}. Error: {e}", file=sys.stderr)
        return []

def analyze_content_strategy(gemini_api_key, video_titles):
    print("\n--- Analyzing Content Strategy (Macro Analysis) ---")
    titles_str = "\n".join(video_titles)
    prompt = f'''As a YouTube content strategy expert, analyze the following list of video titles from a single channel. Based on these titles, identify and summarize the main content pillars or themes of this channel. Provide the output in Chinese as a concise, bulleted list.\n\nVideo Titles:\n---\n{titles_str}\n---'''
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        print("\n[+] Channel Content Strategy Summary:")
        print(analysis)
    else:
        print("\n[-] Could not determine the content strategy.")
    return analysis

def analyze_strategy_evolution(gemini_api_key, all_videos, sample_size=50):
    print("\n--- Analyzing Content Strategy Evolution (Trends Analysis) ---")
    if len(all_videos) < sample_size * 2:
        print(f"\n[-] Not enough videos ({len(all_videos)}) to perform a meaningful trend analysis. At least {sample_size*2} are recommended.")
        return

    newest_videos = all_videos[:sample_size]
    oldest_videos = all_videos[-sample_size:]

    def format_video_list(videos):
        return "\n".join([f"({v['snippet']['publishedAt'][:10]}) {v['snippet']['title']}" for v in videos])

    newest_titles_with_dates = format_video_list(newest_videos)
    oldest_titles_with_dates = format_video_list(oldest_videos)

    prompt = f'''As a senior YouTube strategy consultant, analyze the evolution of a channel's content strategy. I will provide you with a list of the channel's oldest and newest video titles, prefixed with their publication date (YYYY-MM-DD). Your task is to compare these two lists and generate a summary in Chinese, highlighting the changes in content, style, and focus. In your analysis, you MUST use the dates to estimate the approximate time (e.g., 'around mid-2024', 'in the last three months') when these shifts began to occur.\n\nConsider the following:\n- Topic Shift: Has the channel niched down, expanded its topics, or pivoted entirely? When did this happen?\n- Titling Style: Has the titling style changed? Around what time did the new style become prominent?\n- Target Audience: Does the change in topics suggest a change in the target audience? When did this audience shift likely start?\n\nHere is the data:\n\n### Oldest Video Titles:\n{oldest_titles_with_dates}\n\n### Newest Video Titles:\n{newest_titles_with_dates}\n\n### Analysis Summary (in Chinese):\n'''
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        print("\n[+] Content Strategy Evolution Summary:")
        print(analysis)
    else:
        print("\n[-] Could not determine the content strategy evolution.")
    return analysis

def get_video_comments(youtube_service, video_id, max_comments):
    """Fetches top comments for a given video ID, including like counts."""
    comments = []
    try:
        request = youtube_service.commentThreads().list(part="snippet", videoId=video_id, order="relevance", maxResults=max_comments, textFormat="plainText")
        response = request.execute()
        for item in response['items']:
            comment_snippet = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'text': comment_snippet['textDisplay'],
                'like_count': comment_snippet['likeCount']
            })
    except Exception as e:
        if 'disabledComments' in str(e):
            print(f"    - Comments are disabled for video {video_id}. Skipping.")
        else:
            print(f"    - Warning: Could not retrieve comments for video {video_id}. Error: {e}")
    return comments

def summarize_frequent_questions(gemini_api_key, questions):
    """Summarizes a list of questions into frequently asked questions."""
    print("\n--- Summarizing Frequent Questions ---")
    if not questions:
        print("[-] No questions were found in the comments to summarize.")
        return

    questions_str = "\n".join([f"- {q}" for q in questions])
    prompt = f'''As a community manager, analyze the following list of questions extracted from a YouTube comment section. Group them into recurring themes and summarize the top 3-5 most frequently asked questions. Present the result as a concise, bulleted list in Chinese.\n\nQuestions List:\n{questions_str}\n\nTop Frequent Questions Summary:'''
    
    analysis = utils.get_gemini_analysis(gemini_api_key, prompt)
    if analysis:
        print("\n[+] Frequent Questions Summary:")
        print(analysis)
    else:
        print("\n[-] Could not summarize frequent questions.")

def analyze_video_comments(youtube_service, gemini_api_key, videos_to_analyze, comment_limit, output_file):
    """Analyzes comments from a list of videos, saves findings to a CSV, and returns questions."""
    print("\n--- Analyzing Video Comments (Micro Analysis) ---")
    analysis_results = []
    all_questions = []
    
    for video in videos_to_analyze:
        video_id = video['id']
        video_title = video['snippet']['title']
        print(f"\nProcessing video: \"{video_title}\" ")
        
        comments = get_video_comments(youtube_service, video_id, max_comments=comment_limit)
        print(f"  - Fetched {len(comments)} comments for analysis.")

        for comment in comments:
            ai_analysis = utils.analyze_comment_sentiment(gemini_api_key, comment['text'])
            if ai_analysis and ai_analysis.get('category'):
                result = {
                    'video_title': video_title,
                    'video_url': f"https://www.youtube.com/watch?v={video_id}",
                    'comment_text': comment['text'],
                    'like_count': comment['like_count'],
                    'category': ai_analysis['category'],
                    'summary': ai_analysis['summary']
                }
                analysis_results.append(result)
                if ai_analysis['category'] == 'Question':
                    all_questions.append(ai_analysis['summary'])

    if not analysis_results:
        print(f"\n--- No analyzable comments found. ---")
        return []

    # Write CSV
    print(f"\n--- Writing detailed comment analysis to {output_file} ---")
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['video_title', 'video_url', 'category', 'like_count', 'summary', 'comment_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(analysis_results)
        print(f"--- Detailed analysis saved to {output_file} ---")
    except Exception as e:
        print(f"ERROR: Could not write CSV file. Error: {e}", file=sys.stderr)

    # Write HTML Report
    write_html_report(analysis_results, output_file)
    
    return all_questions

def write_html_report(results, output_file):
    """Generates a self-contained, interactive HTML report from the analysis results."""
    html_file_path = output_file.replace('.csv', '.html')
    print(f"--- Generating interactive HTML report to {html_file_path} ---")

    # Simple, clean CSS for the report
    css = """
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; background-color: #f8f9fa; color: #212529; }
        h1 { color: #343a40; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; }
        thead th { background-color: #e9ecef; cursor: pointer; }
        tbody tr:nth-child(even) { background-color: #f2f2f2; }
        tbody tr:hover { background-color: #dee2e6; }
        .controls { margin-bottom: 20px; display: flex; gap: 15px; align-items: center; }
        .controls input, .controls select { padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; }
        .category { padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }
        .Positive-Feedback { background-color: #28a745; }
        .Negative-Sentiment { background-color: #dc3545; }
        .Question { background-color: #007bff; }
        .Suggestion { background-color: #ffc107; color: #212529; }
        .Other { background-color: #6c757d; }
    """

    # JavaScript for filtering and sorting
    js = """
        function filterTable() {
            const keyword = document.getElementById('keywordFilter').value.toLowerCase();
            const category = document.getElementById('categoryFilter').value;
            const table = document.getElementById('resultsTable');
            const rows = table.getElementsByTagName('tr');

            for (let i = 1; i < rows.length; i++) { // Start from 1 to skip header
                const categoryCell = rows[i].getElementsByTagName('td')[0];
                const summaryCell = rows[i].getElementsByTagName('td')[2];
                const commentCell = rows[i].getElementsByTagName('td')[3];
                
                const categoryMatch = (category === '' || categoryCell.textContent.includes(category));
                const keywordMatch = (summaryCell.textContent.toLowerCase().includes(keyword) || commentCell.textContent.toLowerCase().includes(keyword));

                if (categoryMatch && keywordMatch) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        }

        function sortTable(columnIndex) {
            const table = document.getElementById('resultsTable');
            let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            switching = true;
            dir = "asc"; 

            while (switching) {
                switching = false;
                rows = table.rows;
                for (i = 1; i < (rows.length - 1); i++) {
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[columnIndex];
                    y = rows[i + 1].getElementsByTagName("TD")[columnIndex];

                    let xContent = x.innerHTML;
                    let yContent = y.innerHTML;

                    if (columnIndex === 1) { // Like Count column
                        xContent = parseInt(xContent) || 0;
                        yContent = parseInt(yContent) || 0;
                    } else {
                        xContent = xContent.toLowerCase();
                        yContent = yContent.toLowerCase();
                    }

                    if (dir == "asc") {
                        if (xContent > yContent) {
                            shouldSwitch = true;
                            break;
                        }
                    } else if (dir == "desc") {
                        if (xContent < yContent) {
                            shouldSwitch = true;
                            break;
                        }
                    }
                }
                if (shouldSwitch) {
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                } else {
                    if (switchcount == 0 && dir == "asc") {
                        dir = "desc";
                        switching = true;
                    }
                }
            }
        }
    """

    # Build the HTML body
    body = "<h1>YouTube Comment Analysis Report</h1>"
    body += '<div class="controls">'
    body += '<input type="text" id="keywordFilter" onkeyup="filterTable()" placeholder="Filter by keyword...">'
    body += '<select id="categoryFilter" onchange="filterTable()">'
    body += '<option value="">All Categories</option>'
    body += '<option value="Positive Feedback">Positive Feedback</option>'
    body += '<option value="Negative Sentiment">Negative Sentiment</option>'
    body += '<option value="Question">Question</option>'
    body += '<option value="Suggestion">Suggestion</option>'
    body += '<option value="Other">Other</option>'
    body += '</select></div>'

    body += '<table id="resultsTable"><thead><tr>'
    body += '<th onclick="sortTable(0)">Category</th>'
    body += '<th onclick="sortTable(1)">Like Count</th>'
    body += '<th onclick="sortTable(2)">Summary (Translated)</th>'
    body += '<th>Original Comment</th>'
    body += '<th>Video Title</th>'
    body += '</tr></thead><tbody>'

    for r in results:
        category_class = r['category'].replace(' ', '-')
        body += f'<tr>'
        body += f'<td><span class="category {category_class}">{r["category"]}</span></td>'
        body += f'<td>{r["like_count"]}</td>'
        body += f'<td>{r["summary"]}</td>'
        body += f'<td>{r["comment_text"]}</td>'
        body += f'<td>{r["video_title"]}</td>'
        body += f'</tr>'

    body += '</tbody></table>'

    # Combine all parts into a full HTML document
    html_content = f'''<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>YouTube Comment Analysis Report</title>
        <style>{css}</style>
    </head>
    <body>
        {body}
        <script>{js}</script>
    </body>
    </html>'''

    try:
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"--- Successfully generated HTML report. ---")
    except Exception as e:
        print(f"ERROR: Could not write HTML report file. Error: {e}", file=sys.stderr)

def run_youtube_analysis(config, channel_url=None, channel_id=None, video_limit=10, sort_by='popular', analyze_trends=False, comment_limit=15, output_file="youtube_analysis_results.csv"):
    """Main function to run the YouTube channel analysis."""
    print(f"--- Initializing YouTube Analysis Module ---")
    
    youtube_service = get_youtube_service(config)
    if not youtube_service:
        return

    if not channel_id:
        channel_id = get_channel_id_from_url(youtube_service, channel_url)
    
    if not channel_id:
        print("--- YouTube analysis aborted because Channel ID could not be resolved. ---")
        return
    print(f"--- Successfully confirmed Channel ID: {channel_id} ---")

    gemini_api_key = config['GEMINI']['API_KEY']

    if analyze_trends:
        all_videos = get_channel_videos(youtube_service, channel_id, sort_by, video_limit, force_fetch_all=True)
        if all_videos:
            analyze_strategy_evolution(gemini_api_key, all_videos)
    else:
        videos_to_analyze = get_channel_videos(youtube_service, channel_id, sort_by, video_limit)
        if videos_to_analyze:
            if sort_by == 'popular':
                videos_to_analyze.sort(key=lambda v: int(v.get('statistics', {}).get('viewCount', 0)), reverse=True)
                videos_to_analyze = videos_to_analyze[:video_limit]
                print(f"\n--- Selected top {len(videos_to_analyze)} most viewed videos for analysis. ---")

            video_titles = [v['snippet']['title'] for v in videos_to_analyze]
            analyze_content_strategy(gemini_api_key, video_titles)

            questions = analyze_video_comments(youtube_service, gemini_api_key, videos_to_analyze, comment_limit, output_file)
            if questions:
                summarize_frequent_questions(gemini_api_key, questions)
    
    print(f"\n--- YouTube Analysis complete. ---")