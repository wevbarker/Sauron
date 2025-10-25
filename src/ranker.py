"""
Gemini-based collaborator ranking for Sauron
"""

import google.generativeai as genai
from pathlib import Path

from .config import get_google_key


def rank_collaborators(context_file: Path, institution: str) -> str:
    """
    Use Gemini 2.5 Pro to rank potential collaborators

    Args:
        context_file: Path to combined context file
        institution: Institution name

    Returns:
        Ranking text from Gemini
    """

    print(f"\n{'='*60}")
    print(f"Ranking collaborators with Gemini 2.5 Pro")
    print(f"{'='*60}\n")

    # Get API key and configure
    api_key = get_google_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    # Read context
    with open(context_file, 'r') as f:
        context = f.read()

    # Build ranking prompt
    ranking_prompt = f"""You are analyzing potential collaborators at {institution} for academic collaboration and job opportunities.

CONTEXT PROVIDED:
1. My research papers (5 most recent LaTeX sources)
2. My complete publication list (titles & abstracts)
3. My 2025 job applications and research statements
4. Papers (titles, abstracts, citations) for potential collaborators at {institution}

TASK:
Rank the potential collaborators by likelihood of:
- Positive response to cold email about collaboration
- Research compatibility with my work
- Mutual benefit from collaboration
- Potential for job opportunities

IMPORTANT: There are TWO equally important reasons to rank a researcher highly:

1. **EXISTING OVERLAP**: The researcher has published work in areas that overlap with my *past publications*. We share common research topics, methods, or theoretical frameworks based on what I have already done.

2. **FUTURE DIRECTION**: The researcher works in areas that I am *planning to move into*, as stated in my research statements, research plans, or statements of purpose. They may possess skills or expertise in areas I have identified as future goals (e.g., numerical methods, Bayesian inference, data analysis, specific observational techniques) that I need to develop. This is EQUALLY important to existing overlap.

Pay special attention to my research statements and plans to identify what new skills, methods, or research areas I am trying to acquire or pivot towards.

OUTPUT FORMAT:
Return ONLY a ranked list of the top 5-10 researchers in this exact format:

1. [Researcher Name] - [INSPIRE BAI]
   **Research overlap:** [1-2 sentence summary of past work overlap OR future direction alignment]
   **Collaboration potential:** [1-2 sentence assessment]
   **Recommendation:** [Brief reasoning for ranking - specify if this is based on existing overlap, future direction, or both]

2. [Next researcher...]
...

Be concise. Focus on actionable insights about research compatibility.

---

{context}
"""

    print("Sending to Gemini 2.5 Pro (this may take 1-2 minutes)...")

    try:
        response = model.generate_content(ranking_prompt)
        response_text = response.text

        # Get token usage
        if hasattr(response, 'usage_metadata'):
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            print(f"\n✓ Ranking complete!")
            print(f"  Input tokens: {input_tokens:,}")
            print(f"  Output tokens: {output_tokens:,}")
        else:
            print(f"\n✓ Ranking complete!")

        return response_text

    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise
