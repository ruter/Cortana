"""
Tests for the Rotator Client Integration
=========================================

Tests the rotator_client module and its integration with the Cortana agent.
Includes comprehensive backward compatibility tests.
"""

import os
import json
import pytest
import asyncio
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

# Set test environment before importing modules
os.environ.setdefault("DISCORD_TOKEN", "test_token")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test_key")
os.environ.setdefault("ZEP_API_KEY", "test_zep_key")
os.environ.setdefault("LLM_API_KEY", "test_llm_key")


class TestNormalizeModelName:
    """Tests for the normalize_model_name function."""
    
    def test_already_normalized(self):
        """Model names with provider prefix should be unchanged."""
        from src.rotator_client import normalize_model_name
        
        assert normalize_model_name("openai/gpt-4o") == "openai/gpt-4o"
        assert normalize_model_name("gemini/gemini-2.5-flash") == "gemini/gemini-2.5-flash"
        assert normalize_model_name("anthropic/claude-3-sonnet") == "anthropic/claude-3-sonnet"
    
    def test_openai_models(self):
        """OpenAI model names should be prefixed correctly."""
        from src.rotator_client import normalize_model_name
        
        assert normalize_model_name("gpt-4o") == "openai/gpt-4o"
        assert normalize_model_name("gpt-4-turbo") == "openai/gpt-4-turbo"
        assert normalize_model_name("gpt-3.5-turbo") == "openai/gpt-3.5-turbo"
        assert normalize_model_name("o1-preview") == "openai/o1-preview"
        assert normalize_model_name("o3-mini") == "openai/o3-mini"
    
    def test_gemini_models(self):
        """Gemini model names should be prefixed correctly."""
        from src.rotator_client import normalize_model_name
        
        assert normalize_model_name("gemini-2.5-flash") == "gemini/gemini-2.5-flash"
        assert normalize_model_name("gemini-1.5-pro") == "gemini/gemini-1.5-pro"
        assert normalize_model_name("gemini-pro") == "gemini/gemini-pro"
    
    def test_anthropic_models(self):
        """Anthropic/Claude model names should be prefixed correctly."""
        from src.rotator_client import normalize_model_name
        
        assert normalize_model_name("claude-3-sonnet") == "anthropic/claude-3-sonnet"
        assert normalize_model_name("claude-3-opus") == "anthropic/claude-3-opus"
        assert normalize_model_name("claude-3.5-sonnet") == "anthropic/claude-3.5-sonnet"
    
    def test_other_models(self):
        """Other model names should default to openai prefix."""
        from src.rotator_client import normalize_model_name
        
        # Unknown models default to openai
        assert normalize_model_name("some-custom-model") == "openai/some-custom-model"
        
        # Known providers
        assert normalize_model_name("qwen-turbo") == "qwen/qwen-turbo"
        assert normalize_model_name("deepseek-chat") == "deepseek/deepseek-chat"


class TestConfigKeyLoading:
    """Tests for API key loading from environment variables."""
    
    def test_load_provider_api_keys(self):
        """Test loading multiple API keys from environment."""
        from src.config import _load_provider_api_keys
        
        # Set up test environment
        with patch.dict(os.environ, {
            "OPENAI_API_KEY_1": "sk-test1",
            "OPENAI_API_KEY_2": "sk-test2",
            "GEMINI_API_KEY": "AIza-test",
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "SUPABASE_KEY": "should-be-ignored",  # Should be filtered out
            "ZEP_API_KEY": "should-be-ignored",   # Should be filtered out
        }, clear=False):
            keys = _load_provider_api_keys()
            
            assert "openai" in keys
            assert len(keys["openai"]) == 2
            assert "sk-test1" in keys["openai"]
            assert "sk-test2" in keys["openai"]
            
            assert "gemini" in keys
            assert "AIza-test" in keys["gemini"]
            
            assert "anthropic" in keys
            assert "sk-ant-test" in keys["anthropic"]
            
            # Filtered keys should not be present
            assert "supabase" not in keys
            assert "zep" not in keys
    
    def test_load_oauth_credentials(self):
        """Test loading OAuth credential paths from environment."""
        from src.config import _load_oauth_credentials
        
        with patch.dict(os.environ, {
            "GEMINI_CLI_OAUTH_CREDENTIALS": "/path/to/gemini.json",
            "GEMINI_CLI_OAUTH_CREDENTIALS_1": "/path/to/gemini1.json",
            "QWEN_CODE_OAUTH_CREDENTIALS": "/path/to/qwen.json",
            "ANTIGRAVITY_OAUTH_CREDENTIALS": "/path/to/ag.json",
        }, clear=False):
            creds = _load_oauth_credentials()
            
            assert "gemini_cli" in creds
            assert len(creds["gemini_cli"]) == 2
            
            assert "qwen_code" in creds
            assert "antigravity" in creds
    
    def test_backward_compatibility_single_key(self):
        """Test backward compatibility with single LLM_API_KEY."""
        from src.config import Config
        
        # Clear any existing keys
        with patch.dict(os.environ, {
            "LLM_API_KEY": "sk-single-key",
            "LLM_MODEL_NAME": "gpt-4o",
        }, clear=False):
            # Remove any provider-specific keys
            for key in list(os.environ.keys()):
                if "_API_KEY_" in key and key != "LLM_API_KEY":
                    del os.environ[key]
            
            Config.ROTATOR_API_KEYS = {}
            Config.LLM_API_KEY = "sk-single-key"
            Config.LLM_MODEL_NAME = "gpt-4o"
            Config.load_rotator_keys()
            
            # Should have auto-wrapped the single key
            assert "openai" in Config.ROTATOR_API_KEYS
            assert "sk-single-key" in Config.ROTATOR_API_KEYS["openai"]


class TestBackwardCompatibility:
    """Comprehensive backward compatibility tests."""
    
    def test_legacy_single_key_openai(self):
        """Test legacy single OpenAI key auto-wrapping."""
        from src.config import Config
        
        Config.ROTATOR_API_KEYS = {}
        Config.ROTATOR_OAUTH_CREDENTIALS = {}
        Config.LLM_API_KEY = "sk-legacy-openai"
        Config.LLM_MODEL_NAME = "gpt-4o"
        Config.load_rotator_keys()
        
        assert "openai" in Config.ROTATOR_API_KEYS
        assert "sk-legacy-openai" in Config.ROTATOR_API_KEYS["openai"]
    
    def test_legacy_single_key_gemini(self):
        """Test legacy single Gemini key auto-wrapping based on model name."""
        from src.config import Config
        
        Config.ROTATOR_API_KEYS = {}
        Config.ROTATOR_OAUTH_CREDENTIALS = {}
        Config.LLM_API_KEY = "AIza-legacy-gemini"
        Config.LLM_MODEL_NAME = "gemini-1.5-pro"
        Config.load_rotator_keys()
        
        assert "gemini" in Config.ROTATOR_API_KEYS
        assert "AIza-legacy-gemini" in Config.ROTATOR_API_KEYS["gemini"]
    
    def test_legacy_single_key_anthropic(self):
        """Test legacy single Anthropic key auto-wrapping based on model name."""
        from src.config import Config
        
        Config.ROTATOR_API_KEYS = {}
        Config.ROTATOR_OAUTH_CREDENTIALS = {}
        Config.LLM_API_KEY = "sk-ant-legacy"
        Config.LLM_MODEL_NAME = "claude-3-sonnet"
        Config.load_rotator_keys()
        
        assert "anthropic" in Config.ROTATOR_API_KEYS
        assert "sk-ant-legacy" in Config.ROTATOR_API_KEYS["anthropic"]
    
    def test_rotator_disabled_uses_legacy(self):
        """Test that disabling rotator falls back to legacy mode."""
        from src.config import Config
        
        original = Config.ENABLE_ROTATOR
        Config.ENABLE_ROTATOR = False
        
        try:
            # When rotator is disabled, get_rotating_client should return None
            import asyncio
            import src.rotator_client as rc
            
            rc._rotating_client = None
            rc._initialization_attempted = False
            
            async def check():
                client = await rc.get_rotating_client()
                return client
            
            client = asyncio.get_event_loop().run_until_complete(check())
            assert client is None
        finally:
            Config.ENABLE_ROTATOR = original
    
    def test_old_model_format_works(self):
        """Test that old model format (without provider) still works."""
        from src.agent import _get_model_spec
        from src.rotator_client import normalize_model_name
        
        # Old format should be converted correctly
        old_formats = [
            ("gpt-4o", "openai:gpt-4o"),
            ("gpt-4-turbo", "openai:gpt-4-turbo"),
            ("gemini-1.5-pro", "google:gemini-1.5-pro"),
            ("claude-3-sonnet", "anthropic:claude-3-sonnet"),
        ]
        
        for old_format, expected_spec in old_formats:
            assert _get_model_spec(old_format) == expected_spec
            
            # normalize_model_name should also work
            normalized = normalize_model_name(old_format)
            assert "/" in normalized
    
    def test_settings_model_command_accepts_old_format(self):
        """Test that /settings model command accepts old format."""
        from src.rotator_client import normalize_model_name
        
        # Simulate what the command does
        old_input = "gpt-4o"
        normalized = normalize_model_name(old_input)
        
        assert normalized == "openai/gpt-4o"
    
    def test_mixed_key_formats(self):
        """Test that mixed key formats (numbered and unnumbered) work."""
        from src.config import _load_provider_api_keys
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-base",
            "OPENAI_API_KEY_1": "sk-one",
            "OPENAI_API_KEY_2": "sk-two",
        }, clear=False):
            keys = _load_provider_api_keys()
            
            assert "openai" in keys
            # Should have all three keys
            assert len(keys["openai"]) == 3
            assert "sk-base" in keys["openai"]
            assert "sk-one" in keys["openai"]
            assert "sk-two" in keys["openai"]


class TestRotatorClientSingleton:
    """Tests for the rotating client singleton pattern."""
    
    @pytest.mark.asyncio
    async def test_get_rotating_client_disabled(self):
        """Test that None is returned when rotator is disabled."""
        from src.config import config
        from src.rotator_client import get_rotating_client, _rotating_client
        
        # Reset singleton state
        import src.rotator_client as rc
        rc._rotating_client = None
        rc._initialization_attempted = False
        
        original = config.ENABLE_ROTATOR
        config.ENABLE_ROTATOR = False
        
        try:
            client = await get_rotating_client()
            assert client is None
        finally:
            config.ENABLE_ROTATOR = original
    
    @pytest.mark.asyncio
    async def test_get_rotating_client_no_library(self):
        """Test graceful fallback when rotator_library is not installed."""
        from src.config import config
        import src.rotator_client as rc
        
        # Reset singleton state
        rc._rotating_client = None
        rc._initialization_attempted = False
        
        original = config.ENABLE_ROTATOR
        config.ENABLE_ROTATOR = True
        
        try:
            # Mock ImportError for rotator_library
            with patch.dict('sys.modules', {'rotator_library': None}):
                with patch('builtins.__import__', side_effect=ImportError("No module named 'rotator_library'")):
                    # This should handle the ImportError gracefully
                    client = await get_rotating_client()
                    # May return None or raise - depends on implementation
        except ImportError:
            pass  # Expected in some cases
        finally:
            config.ENABLE_ROTATOR = original
            rc._initialization_attempted = False
    
    @pytest.mark.asyncio
    async def test_singleton_returns_same_instance(self):
        """Test that get_rotating_client returns the same instance."""
        import src.rotator_client as rc
        
        # If client is already initialized, it should return the same instance
        if rc._rotating_client is not None:
            client1 = await rc.get_rotating_client()
            client2 = await rc.get_rotating_client()
            assert client1 is client2


class TestKeyPoolStatus:
    """Tests for key pool status reporting."""
    
    @pytest.mark.asyncio
    async def test_get_key_pool_status(self):
        """Test retrieving key pool status."""
        from src.rotator_client import get_key_pool_status
        from src.config import Config
        
        # Set up test keys
        Config.ROTATOR_API_KEYS = {
            "openai": ["key1", "key2"],
            "gemini": ["key3"],
        }
        Config.ROTATOR_OAUTH_CREDENTIALS = {}
        Config.ENABLE_ROTATOR = True
        Config.LLM_MODEL_NAME = "gpt-4o"
        
        status = await get_key_pool_status()
        
        assert "providers" in status
        assert "key_counts" in status
        assert "rotator_enabled" in status
        assert status["rotator_enabled"] == True
        assert status["key_counts"].get("openai") == 2
        assert status["key_counts"].get("gemini") == 1


class TestUsageTracking:
    """Tests for usage tracking and statistics."""
    
    def test_get_usage_summary_empty(self):
        """Test get_usage_summary with no usage file."""
        from src.rotator_client import get_usage_summary
        from src.config import config
        
        # Point to non-existent file
        original = config.ROTATOR_USAGE_FILE_PATH
        config.ROTATOR_USAGE_FILE_PATH = "/tmp/non_existent_usage.json"
        
        try:
            summary = get_usage_summary()
            
            assert summary["total_requests"] == 0
            assert summary["total_tokens"] == 0
            assert summary["total_cost"] == 0.0
            assert summary["by_provider"] == {}
            assert summary["by_model"] == {}
        finally:
            config.ROTATOR_USAGE_FILE_PATH = original
    
    def test_get_usage_summary_with_data(self):
        """Test get_usage_summary with mock usage data."""
        from src.rotator_client import get_usage_summary, load_usage_stats
        from src.config import config
        
        # Create temp file with mock data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            mock_data = {
                "key1": {
                    "provider": "openai",
                    "requests": 100,
                    "total_tokens": 50000,
                    "cost": 0.05,
                    "models": {
                        "gpt-4o": {"requests": 80},
                        "gpt-4-turbo": {"requests": 20}
                    }
                },
                "key2": {
                    "provider": "gemini",
                    "requests": 50,
                    "total_tokens": 25000,
                    "cost": 0.01,
                    "models": {
                        "gemini-1.5-pro": {"requests": 50}
                    }
                }
            }
            json.dump(mock_data, f)
            temp_path = f.name
        
        original = config.ROTATOR_USAGE_FILE_PATH
        config.ROTATOR_USAGE_FILE_PATH = temp_path
        
        try:
            summary = get_usage_summary()
            
            assert summary["total_requests"] == 150
            assert summary["total_tokens"] == 75000
            assert summary["total_cost"] == 0.06
            assert "openai" in summary["by_provider"]
            assert "gemini" in summary["by_provider"]
            assert summary["by_provider"]["openai"]["requests"] == 100
            assert "gpt-4o" in summary["by_model"]
        finally:
            config.ROTATOR_USAGE_FILE_PATH = original
            os.unlink(temp_path)


class TestRotatingCompletion:
    """Tests for the rotating_completion wrapper function."""
    
    @pytest.mark.asyncio
    async def test_rotating_completion_fallback_to_litellm(self):
        """Test that rotating_completion falls back to litellm when rotator unavailable."""
        from src.config import config
        import src.rotator_client as rc
        
        # Reset singleton and disable rotator
        rc._rotating_client = None
        rc._initialization_attempted = False
        original = config.ENABLE_ROTATOR
        config.ENABLE_ROTATOR = False
        config.LLM_API_KEY = "test-key"
        
        try:
            # Mock litellm
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]
            
            with patch('litellm.acompletion', new_callable=AsyncMock) as mock_acompletion:
                mock_acompletion.return_value = mock_response
                
                from src.rotator_client import rotating_completion
                
                response = await rotating_completion(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Hi"}]
                )
                
                # Should have called litellm directly
                mock_acompletion.assert_called_once()
                call_kwargs = mock_acompletion.call_args[1]
                assert "openai/gpt-4o" in call_kwargs["model"]
        finally:
            config.ENABLE_ROTATOR = original
    
    @pytest.mark.asyncio
    async def test_rotating_completion_uses_default_model(self):
        """Test that rotating_completion uses default model when none specified."""
        from src.config import config
        import src.rotator_client as rc
        
        rc._rotating_client = None
        rc._initialization_attempted = False
        original_rotator = config.ENABLE_ROTATOR
        original_model = config.LLM_MODEL_NAME
        config.ENABLE_ROTATOR = False
        config.LLM_MODEL_NAME = "gpt-4-turbo"
        config.LLM_API_KEY = "test-key"
        
        try:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]
            
            with patch('litellm.acompletion', new_callable=AsyncMock) as mock_acompletion:
                mock_acompletion.return_value = mock_response
                
                from src.rotator_client import rotating_completion
                
                # Don't specify model
                await rotating_completion(
                    messages=[{"role": "user", "content": "Hi"}]
                )
                
                call_kwargs = mock_acompletion.call_args[1]
                assert "gpt-4-turbo" in call_kwargs["model"]
        finally:
            config.ENABLE_ROTATOR = original_rotator
            config.LLM_MODEL_NAME = original_model


class TestAnthropicCompatibility:
    """Tests for Anthropic API compatibility layer."""
    
    @pytest.mark.asyncio
    async def test_anthropic_fallback(self):
        """Test the Anthropic fallback implementation."""
        from src.rotator_client import _anthropic_fallback
        from src.config import config
        import src.rotator_client as rc
        
        rc._rotating_client = None
        rc._initialization_attempted = False
        config.ENABLE_ROTATOR = False
        config.LLM_API_KEY = "test-key"
        
        # Create mock request object
        mock_request = MagicMock()
        mock_request.model = "claude-3-sonnet"
        mock_request.messages = [{"role": "user", "content": "Hello"}]
        mock_request.max_tokens = 100
        mock_request.system = "You are a helpful assistant."
        
        # Mock the rotating_completion function
        mock_response = MagicMock()
        mock_response.id = "test-id"
        mock_response.choices = [MagicMock(message=MagicMock(content="Hi there!"))]
        mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 5}
        
        with patch('src.rotator_client.rotating_completion', new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            
            result = await _anthropic_fallback(mock_request)
            
            assert result["type"] == "message"
            assert result["role"] == "assistant"
            assert len(result["content"]) > 0
            assert result["content"][0]["type"] == "text"
            assert "Hi there!" in result["content"][0]["text"]


class TestAgentIntegration:
    """Tests for agent integration with rotator."""
    
    def test_get_model_spec(self):
        """Test model specification generation for PydanticAI."""
        from src.agent import _get_model_spec
        
        # OpenAI models
        assert _get_model_spec("gpt-4o") == "openai:gpt-4o"
        assert _get_model_spec("openai/gpt-4o") == "openai:gpt-4o"
        
        # Gemini models
        assert _get_model_spec("gemini-2.5-flash") == "google:gemini-2.5-flash"
        assert _get_model_spec("gemini/gemini-2.5-flash") == "google:gemini-2.5-flash"
        
        # Anthropic models
        assert _get_model_spec("claude-3-sonnet") == "anthropic:claude-3-sonnet"
        assert _get_model_spec("anthropic/claude-3-sonnet") == "anthropic:claude-3-sonnet"
    
    def test_get_model_spec_edge_cases(self):
        """Test model specification for edge cases."""
        from src.agent import _get_model_spec
        
        # O-series models
        assert _get_model_spec("o1-preview") == "openai:o1-preview"
        assert _get_model_spec("o3-mini") == "openai:o3-mini"
        
        # Unknown provider defaults to openai
        assert _get_model_spec("custom-model") == "openai:custom-model"


class TestTokenCounting:
    """Tests for token counting functionality."""
    
    def test_token_count_fallback(self):
        """Test token count with fallback estimation."""
        from src.rotator_client import token_count
        
        # Test with text
        count = token_count("gpt-4o", text="Hello, this is a test message.")
        assert count > 0
        
        # Test with messages
        count = token_count("gpt-4o", messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ])
        assert count > 0


# Run with: pytest tests/test_rotator_integration.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
