import boto3

polly = boto3.client("polly")

import re

VOICE_CONFIG = {
    "en": {
        "voice": "Joanna",
        "lang": "en-US",
    },
    "hi": {
        "voice": "Aditi",
        "lang": "hi-IN",
    },
    "mr": {
        "voice": "Aditi",
        "lang": "hi-IN",
    },
    "bn": {
        "voice": "Aditi",
        "lang": "hi-IN",
    },
    "ml": {
        "voice": "Aditi",
        "lang": "hi-IN",
    },
    "ta": {
        "voice": "Valli",
        "lang": "ta-IN",
    },
    "te": {
        "voice": "Vani",
        "lang": "te-IN",
    },
}

def strip_markdown(text: str) -> str:
    """
    Remove common markdown symbols that Polly might read incorrectly.
    """
    # Remove headers (#)
    text = re.sub(r'#+\s*', '', text)
    # Remove bold/italic (**)
    text = re.sub(r'\*+', '', text)
    # Remove list markers (-)
    text = re.sub(r'^\s*[-*+]\s+', ' ', text, flags=re.MULTILINE)
    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def synthesize_speech(text: str, language: str = "en") -> bytes:
    """
    Synthesize speech using Amazon Polly and return raw audio bytes.

    Uses a safe configuration with language-specific voices and
    falls back to English (Joanna) if Polly raises any error.
    """
    text = strip_markdown(text)
    config = VOICE_CONFIG.get(language, VOICE_CONFIG["en"])

    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=config["voice"],
            LanguageCode=config["lang"],
            Engine="neural"
        )
        return response["AudioStream"].read()

    except Exception:
        # fallback to English if anything fails
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            LanguageCode="en-US",
            Engine="neural"
        )
        return response["AudioStream"].read()
