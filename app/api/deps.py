from app.providers.ai_factory import get_ai_provider

def ai_provider_dep():
    return get_ai_provider()
