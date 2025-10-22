

import google.generativeai as genai
import json
import sys
import urllib.request
import pathlib
import mimetypes

def get_gemini_analysis(gemini_api_key, prompt, is_json_output=False):
    """
    Calls the Gemini API with a specific prompt and returns the analysis.

    Args:
        gemini_api_key (str): The API key for Gemini.
        prompt (str): The full prompt to send to the model.
        is_json_output (bool): If True, will attempt to parse the response as JSON.

    Returns:
        The raw text response, or a parsed JSON dictionary, or None on failure.
    """
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
    except Exception as e:
        print(f"ERROR: Failed to configure Gemini API. Check your key. Error: {e}", file=sys.stderr)
        return None # Return None instead of raising to allow graceful failure

    response = None
    try:
        response = model.generate_content(prompt)
        
        if is_json_output:
            # Clean up potential markdown JSON formatting
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_response)
        else:
            return response.text.strip()

    except Exception as e:
        print(f"ERROR: An error occurred during Gemini API call or parsing. Error: {e}", file=sys.stderr)
        if response:
            print(f"Gemini raw response was: {response.text}", file=sys.stderr)
        return None

def analyze_post_with_gemini(gemini_api_key, post_title, post_text):
    """Analyzes a single piece of text using the Gemini API to find problems."""
    prompt = f'''
    Analyze the following text from a social media post with the title "{post_title}". 
    Determine if it expresses a problem, question, or negative feedback. 
    
    Text to analyze: "{post_text}"
    
    Respond ONLY with a JSON object with the following structure:
    {{
      "is_problem_post": boolean, (true if it contains a problem, question, or negative feedback, otherwise false)
      "problem_summary": "If true, provide a concise summary in Chinese. Otherwise, null.",
      "tags": ["If true, provide relevant tags in Chinese, like '功能请求', '使用疑问', '购买咨询', '程序错误', '体验抱怨'. Otherwise, an empty array."]
    }}
    '''
    return get_gemini_analysis(gemini_api_key, prompt, is_json_output=True)

def analyze_comment_sentiment(gemini_api_key, comment_text):
    """Analyzes a single YouTube comment for sentiment and categorization."""
    prompt = f'''
    Analyze the following YouTube comment and classify it. Your response must be a JSON object.

    Comment: "{comment_text}"

    Respond with a JSON object using the following structure:
    {{
        "category": "string", // Must be one of: ["Positive Feedback", "Negative Sentiment", "Question", "Suggestion", "Other"]
        "summary": "string" // Paraphrase the original comment into natural-sounding, fluent Chinese, capturing the user's tone and core message. Do not summarize, but rephrase it elegantly.
    }}
    '''
    return get_gemini_analysis(gemini_api_key, prompt, is_json_output=True)

def analyze_comments_batch(gemini_api_key, comments):
    """
    Analyzes a batch of YouTube comments using a single Gemini API call.

    Args:
        gemini_api_key (str): The API key for Gemini.
        comments (list): A list of comment dictionaries, each with an 'id' and 'text'.

    Returns:
        A dictionary mapping comment IDs to their analysis results, or None on failure.
    """
    # Create a numbered list of comments for the prompt
    prompt_comments = []
    for i, comment in enumerate(comments):
        # Use a simple index as the ID for this batch
        comment['id'] = i 
        prompt_comments.append(f'{i}: "{comment["text"]}"')

    prompt_comments_str = "\n".join(prompt_comments)

    prompt = f'''
    Analyze each of the following YouTube comments, which are provided as a numbered list.
    Your response MUST be a single valid JSON object. This object should contain a single key, "results", which is an array of JSON objects.
    Each object in the "results" array must correspond to a comment from the input and have the following structure:
    {{
        "id": integer, // The original number (ID) of the comment from the input list.
        "category": "string", // Must be one of: ["Positive Feedback", "Negative Sentiment", "Question", "Suggestion", "Other"]
        "summary": "string" // Paraphrase the original comment into natural-sounding, fluent Chinese, capturing the user's tone and core message.
    }}

    Here is the list of comments to analyze:
    ---
    {prompt_comments_str}
    ---

    Provide your response as a single JSON object with the "results" key.
    '''
    
    analysis_result = get_gemini_analysis(gemini_api_key, prompt, is_json_output=True)

    if analysis_result and 'results' in analysis_result:
        # Remap the list of results into a dictionary keyed by the original comment ID
        # This makes it easy to look up results for each comment.
        return {result['id']: result for result in analysis_result['results']}
    else:
        print(f"ERROR: Batch comment analysis failed to produce valid results.", file=sys.stderr)
        return None

def analyze_thumbnails_style(gemini_api_key, image_urls):
    """
    Analyzes a batch of YouTube thumbnail images using a single multimodal Gemini API call.
    """
    print(f"--- Analyzing {len(image_urls)} thumbnails ---")
    
    image_parts = []
    for url in image_urls:
        try:
            # Download the image from the URL
            with urllib.request.urlopen(url) as response:
                image_data = response.read()
                mime_type = response.info().get_content_type()
                if not mime_type:
                    mime_type = mimetypes.guess_type(url)[0]
                
                if mime_type and mime_type.startswith("image/"):
                    image_parts.append({'mime_type': mime_type, 'data': image_data})
                else:
                    print(f"Warning: Skipped URL with non-image mime_type: {mime_type} from {url}", file=sys.stderr)

        except Exception as e:
            print(f"Warning: Could not download or process image from {url}. Error: {e}", file=sys.stderr)
            continue

    if not image_parts:
        print("ERROR: No valid images could be downloaded for analysis.", file=sys.stderr)
        return None

    # Construct the multimodal prompt
    prompt_parts = [
        """As an expert YouTube channel art director, analyze the following thumbnail images from a single channel.
For each image, provide a brief, one-sentence analysis covering the following aspects:
1.  **Composition & Subject:** What is the main subject and how is it framed? (e.g., "Close-up on a person's expressive face on the right," "Clean product shot in the center.")
2.  **Color & Mood:** What is the dominant color scheme and the mood it creates? (e.g., "High-contrast with vibrant yellows, creating an energetic mood.")
3.  **Text & Typography:** Is there text? If so, describe its style. (e.g., "Bold, white, sans-serif text with a red outline for high readability.")

After analyzing all images individually, provide a "## Overall Summary" section. In this summary, identify the common patterns and the overall visual strategy of this channel's thumbnails.
Please provide the entire output in Chinese, formatted as Markdown.

---
IMAGES:
""",
        *image_parts
    ]

    try:
        genai.configure(api_key=gemini_api_key)
        # Use a model that supports vision
        model = genai.GenerativeModel('gemini-pro-vision')
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        print(f"ERROR: An error occurred during Gemini multimodal API call. Error: {e}", file=sys.stderr)
        return "Error: AI analysis of thumbnails failed."

