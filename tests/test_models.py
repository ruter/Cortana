import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import MODELS, get_model, get_providers, get_models, find_model_by_id

def test_get_providers():
    providers = get_providers()
    assert "openai" in providers
    assert "anthropic" in providers
    assert "google" in providers

def test_get_models():
    openai_models = get_models("openai")
    assert len(openai_models) > 0
    assert any(m.id == "gpt-4o" for m in openai_models)

def test_get_model():
    model = get_model("openai", "gpt-4o")
    assert model is not None
    assert model.name == "GPT-4o"
    assert model.provider == "openai"

def test_find_model_by_id():
    model = find_model_by_id("claude-3-5-sonnet-20241022")
    assert model is not None
    assert model.provider == "anthropic"
    
    model = find_model_by_id("non-existent")
    assert model is None

if __name__ == "__main__":
    pytest.main([__file__])
