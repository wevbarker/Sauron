"""
Configuration and API key management for Sauron
"""

import os
import sys

def get_openai_key():
    """Get OpenAI API key from environment"""
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return key


def get_google_key():
    """Get Google API key from environment"""
    # Try Martensite's key_discovery first if available
    try:
        from pathlib import Path
        martensite_path = Path.home() / "Documents" / "Martensite"
        if martensite_path.exists():
            sys.path.insert(0, str(martensite_path))
            from martensite.key_discovery import get_api_key
            key = get_api_key('google')
            if key:
                return key
    except ImportError:
        pass

    # Fallback to environment variables
    key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not key:
        print("Error: No Google API key found.", file=sys.stderr)
        print("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)
    return key


# API endpoints
OPENAI_BASE_URL = "https://api.openai.com/v1"
INSPIRE_API_BASE = "https://inspirehep.net/api"
