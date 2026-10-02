"""Extract configuration names, never their values, from example configuration."""

import re
from pathlib import PurePosixPath

PROVIDERS = {
    'openai': ('OpenAI', 'OPENAI_API_KEY'),
    'gemini': ('Google Gemini', 'GEMINI_API_KEY'),
    'anthropic': ('Anthropic', 'ANTHROPIC_API_KEY'),
    'deepseek': ('DeepSeek', 'DEEPSEEK_API_KEY'),
    'openrouter': ('OpenRouter', 'OPENROUTER_API_KEY'),
    'groq': ('Groq', 'GROQ_API_KEY'),
    'huggingface': ('Hugging Face', 'HF_TOKEN'),
    'mistral': ('Mistral', 'MISTRAL_API_KEY'),
    'cohere': ('Cohere', 'COHERE_API_KEY'),
    'replicate': ('Replicate', 'REPLICATE_API_TOKEN'),
    'elevenlabs': ('ElevenLabs', 'ELEVENLABS_API_KEY'),
    'assemblyai': ('AssemblyAI', 'ASSEMBLYAI_API_KEY'),
    'supabase': ('Supabase — отдельный тестовый проект', 'SUPABASE_SERVICE_ROLE_KEY'),
    'firebase': ('Firebase — отдельный тестовый проект', 'FIREBASE_API_KEY'),
    'telegram': ('Telegram — отдельный тестовый бот', 'TELEGRAM_BOT_TOKEN'),
    'twilio': ('Twilio', 'TWILIO_AUTH_TOKEN'),
    'sendgrid': ('SendGrid', 'SENDGRID_API_KEY'),
    'resend': ('Resend', 'RESEND_API_KEY'),
    'mapbox': ('Mapbox', 'MAPBOX_ACCESS_TOKEN'),
    'maps': ('Google Maps / 2GIS / Yandex — уточнить сервис', 'MAPS_API_KEY'),
    'pinecone': ('Pinecone — отдельный индекс', 'PINECONE_API_KEY'),
    'qdrant': ('Qdrant — облако либо локальный сервис', 'QDRANT_API_KEY'),
    'aws': ('AWS / S3 — отдельные тестовые ресурсы', 'AWS_ACCESS_KEY_ID'),
    'azure': ('Azure — endpoint, deployment и ключ', 'AZURE_OPENAI_API_KEY'),
    'cloudinary': ('Cloudinary', 'CLOUDINARY_API_SECRET'),
    'stripe': ('Stripe — только test mode', 'STRIPE_SECRET_KEY'),
    'google_unknown': ('Google API — назначение нужно уточнить', 'GOOGLE_API_KEY'),
    'unknown': ('Не удалось определить сервис', None),
}
SKIP = {'node_modules', '.git', 'venv', '.venv', 'vendor', 'dist', 'build', '.next'}
NAME = re.compile(r'^\s*(?:[-#]\s*)?(?:export\s+)?[\"\']?([A-Z][A-Z0-9_]{2,100})[\"\']?\s*[:=]')
INTERPOLATION = re.compile(r'\$\{([A-Z][A-Z0-9_]{2,100})(?=[:}?\-])')


def candidate(path):
    parts = PurePosixPath(path.lower()).parts
    if not parts:
        return False
    if any(part in SKIP for part in parts):
        return False
    name = parts[-1]
    if PurePosixPath(name).suffix in {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.mp4', '.xlsx', '.parquet'}:
        return False
    return (('env' in name or 'secret' in name or 'config' in name)
            and any(word in name for word in ('example', 'sample', 'template', 'dist'))
            or name in {'compose.yml', 'compose.yaml', 'docker-compose.yml', 'docker-compose.yaml'}
            or name in {'readme', 'readme.md', 'readme.txt', 'readme.rst', 'readme.markdown'}
            or (name.startswith('readme.') and PurePosixPath(name).suffix in {'.md', '.txt', '.rst'}))


def classify(name):
    n = name.upper()
    provider = next((p for p, pattern in (
        ('azure', r'AZURE'), ('openrouter', r'OPENROUTER'), ('deepseek', r'DEEPSEEK'),
        ('anthropic', r'ANTHROPIC|CLAUDE'), ('gemini', r'GEMINI|GOOGLE_AI'),
        ('openai', r'OPENAI'), ('groq', r'GROQ'), ('huggingface', r'HUGGING|^HF_'),
        ('mistral', r'MISTRAL'), ('cohere', r'COHERE'), ('replicate', r'REPLICATE'),
        ('elevenlabs', r'ELEVEN'), ('assemblyai', r'ASSEMBLY'), ('supabase', r'SUPABASE'),
        ('firebase', r'FIREBASE'), ('telegram', r'TELEGRAM|^TG_|^BOT_TOKEN$'),
        ('twilio', r'TWILIO'), ('sendgrid', r'SENDGRID'), ('resend', r'RESEND'),
        ('mapbox', r'MAPBOX'), ('maps', r'MAPS|2GIS|DGIS|YANDEX'),
        ('pinecone', r'PINECONE'), ('qdrant', r'QDRANT'), ('aws', r'AWS|^S3_'),
        ('cloudinary', r'CLOUDINARY'), ('stripe', r'STRIPE'),
        ('google_unknown', r'GOOGLE_API_KEY'),
    ) if re.search(pattern, n)), None)
    secret = bool(re.search(r'KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|PRIVATE', n))
    if provider:
        return provider, 'external_credential' if secret else 'service_config'
    if re.search(r'JWT|SESSION_SECRET|AUTH_SECRET|SECRET_KEY|APP_KEY|ENCRYPTION_KEY', n):
        return None, 'local_secret'
    if re.search(r'DATABASE|POSTGRES|MYSQL|MONGO|REDIS|DB_', n):
        return None, 'local_service'
    if secret:
        return 'unknown', 'unknown_credential'
    return None, 'setting'


def extract(text, path):
    """Values and comments may contain real secrets even in examples; never return them."""
    found = {}
    for number, line in enumerate(text.splitlines(), 1):
        match = NAME.match(line)
        names = ([match.group(1)] if match else []) + INTERPOLATION.findall(line)
        for name in names:
            provider, kind = classify(name)
            if name not in found:
                found[name] = {'name': name, 'provider': provider, 'kind': kind,
                               'required': 'unknown', 'path': path, 'line': number}
    return list(found.values())
