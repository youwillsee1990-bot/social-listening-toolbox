

import google.generativeai as genai
import json
import sys

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

