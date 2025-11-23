translate_prompt = """
                You are a professional translator specializing in user queries written in natural language for discovering GitHub repositories.  
                Translate the following Korean text into concise, clear, and natural English suitable for embedding or semantic similarity search.  
                If the input is already in English, return it unchanged.  
                Keep the original meaning and terminology, but adjust the phrasing to improve relevance.  
                Do NOT include or imply any words related to searching actions, such as "search", "find", "look for", "discover", "seek", "retrieve", or any of their synonyms.  
                Focus purely on expressing the user’s intent or topic, not the act of searching.  
                Text to translate: {question}
                Return only the English translation with no explanations or additional text.
            """

search_query_prompt = """
        Current Date: {{ current_date }}
        You are a GitHub search expert who converts natural language requests into valid GitHub Search API queries.

        Your task:
        - Read the user’s natural language request (`question`).
        - Refer to the provided `context`, which explains how GitHub search qualifiers (e.g., stars, language, good-first-issues, label, topic, repo, sort) are used.
        {% if languages and languages|length > 0 -%}
        - Use the user’s selected `languages` list to include language filters where appropriate.
          For example:
            - language:javascript
            - language:"regular expression"
        {%- endif %}

        ### Rules
        1) If a qualifier schema contains one or more spaces, wrap the entire schema in double quotes (" ").
           - Examples: label:"in progress", topic:"machine learning"
        2) GitHub search is case-insensitive; prefer lowercase for consistency.
        3) Follow the syntax and examples described in the provided `context`.
        4) Output only a single GitHub search question string (no explanations).
        5) If intent is unclear, infer the most likely goal using the context.

        ### Inputs
        - question: {{ question }}
        - context: {{ context }}
        {% if languages and languages|length > 0 -%}
        - languages: {{ languages }}
        {%- endif %}

        ### Output
        Return only the GitHub Search question string.
        """

simple_summary_prompt = """
    You are a GitHub repository summarizer.

    Summarize each repository in Korean.
    Return an array where each item has exactly 3 bullet points.
    Follow these simple rules:

    1. What the repository does (its purpose).
    2. Important features based only on description, languages, and topics.
    3. Typical use cases or why it is useful. Do not mention stars or popularity.

    Do not guess. Use only the information provided.

    Repository list:
    {repo_list}
"""

simple_summary_prompt_async = """
    You are a GitHub repository summarizer.
    
    You will receive a single GitHub repository metadata object.
    Summarize this repository in Korean using exactly 3 bullet points.
    
    Follow these rules:
    1. Explain what the repository does and what it is used for.
    2. Describe important features based only on the description, languages, and topics.
    3. Describe typical use cases or why it is useful. Do not mention stars, forks, or other popularity metrics.
    
    Do not guess. Use only the information provided.
    
    Repository:
    {repo}
"""
