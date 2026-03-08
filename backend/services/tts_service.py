import boto3

polly = boto3.client("polly")

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


def synthesize_speech(text: str, language: str = "en") -> bytes:
    """
    Synthesize speech using Amazon Polly and return raw audio bytes.

    Uses a safe configuration with language-specific voices and
    falls back to English (Joanna) if Polly raises any error.
    """
    config = VOICE_CONFIG.get(language, VOICE_CONFIG["en"])

    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=config["voice"],
            LanguageCode=config["lang"],
        )
        return response["AudioStream"].read()

    except Exception:
        # fallback to English if anything fails
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            LanguageCode="en-US",
        )
        return response["AudioStream"].read()
