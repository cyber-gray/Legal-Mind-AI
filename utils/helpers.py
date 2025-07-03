"""
Utility functions for Legal-Mind-AI
"""

import re
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

def extract_email_from_text(text: str) -> Optional[str]:
    """
    Extract email address from text using regex
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def clean_text_for_analysis(text: str) -> str:
    """
    Clean text for better analysis by removing extra whitespace and formatting
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might interfere with analysis
    text = re.sub(r'[^\w\s\-.,!?:;()]', '', text)
    
    return text.strip()

def generate_session_id(user_id: str) -> str:
    """
    Generate a unique session ID for tracking conversations
    """
    timestamp = datetime.now().isoformat()
    content = f"{user_id}_{timestamp}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amounts for display
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse various date string formats
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%B %d, %Y",
        "%b %d, %Y",
        "%m/%d/%Y",
        "%d/%m/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract potential keywords from text
    """
    # Simple keyword extraction - split on whitespace and punctuation
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter by length and remove common stop words
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
        'have', 'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how',
        'their', 'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so'
    }
    
    keywords = [word for word in words 
                if len(word) >= min_length and word not in stop_words]
    
    return list(set(keywords))  # Remove duplicates

def validate_config(config_dict: Dict[str, Any], required_keys: List[str]) -> List[str]:
    """
    Validate configuration dictionary and return missing keys
    """
    missing_keys = []
    
    for key in required_keys:
        if key not in config_dict or not config_dict[key]:
            missing_keys.append(key)
    
    return missing_keys

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback to default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def create_response_metadata(
    user_id: str,
    query: str,
    processing_time: float,
    agents_used: List[str],
    confidence_score: float = 0.8
) -> Dict[str, Any]:
    """
    Create metadata for agent responses
    """
    return {
        "user_id": user_id,
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "processing_time_seconds": round(processing_time, 2),
        "agents_used": agents_used,
        "confidence_score": confidence_score,
        "session_id": generate_session_id(user_id)
    }

def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data like emails, phone numbers, etc. in text
    """
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  '[EMAIL_MASKED]', text)
    
    # Mask phone numbers (simple patterns)
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE_MASKED]', text)
    text = re.sub(r'\b\(\d{3}\)\s\d{3}-\d{4}\b', '[PHONE_MASKED]', text)
    
    # Mask potential API keys or tokens (long alphanumeric strings)
    text = re.sub(r'\b[A-Za-z0-9]{32,}\b', '[TOKEN_MASKED]', text)
    
    return text
