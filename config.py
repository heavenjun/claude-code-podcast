# Speaker configuration for Gemini TTS MultiSpeakerVoiceConfig
SPEAKERS = [
    {"name": "田中", "gender": "male", "voice": "Charon"},
    {"name": "鈴木", "gender": "female", "voice": "Aoede"},
]

# Google Drive upload destination
DRIVE_FOLDER_NAME = "Podcasts"

# GitHub repo for Claude Code releases (owner/repo)
GITHUB_REPO = "anthropics/claude-code"

# Topic label used in research prompts
PODCAST_TOPIC = "Claude Code"

# File tracking which versions have been processed
PROCESSED_VERSIONS_FILE = "processed_versions.json"

# Directory for intermediate output files
OUTPUT_DIR = "output"

# Number of dialogue turns to send per TTS API call
TTS_CHUNK_SIZE = 8

# Gemini model for research + script generation
GEMINI_RESEARCH_MODEL = "gemini-2.0-flash"
GEMINI_SCRIPT_MODEL = "gemini-2.0-flash"

# Gemini model for TTS
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

# Audio settings (Gemini TTS outputs PCM 24kHz 16-bit mono)
AUDIO_SAMPLE_RATE = 24000
AUDIO_CHANNELS = 1
AUDIO_SAMPLE_WIDTH = 2  # bytes (16-bit)
