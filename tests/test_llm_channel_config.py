# -*- coding: utf-8 -*-
"""Tests for env-based LLM channel parsing."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import Config, extra_litellm_params


class LLMChannelConfigTestCase(unittest.TestCase):
    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_protocol_prefixes_bare_model_names(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "primary",
            "LLM_PRIMARY_PROTOCOL": "deepseek",
            "LLM_PRIMARY_BASE_URL": "https://api.deepseek.com/v1",
            "LLM_PRIMARY_API_KEY": "sk-test-value",
            "LLM_PRIMARY_MODELS": "deepseek-chat",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(config.llm_models_source, "llm_channels")
        self.assertEqual(config.llm_channels[0]["protocol"], "deepseek")
        self.assertEqual(config.llm_channels[0]["models"], ["deepseek/deepseek-chat"])
        self.assertEqual(config.llm_model_list[0]["litellm_params"]["model"], "deepseek/deepseek-chat")

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_openai_compatible_channel_prefixes_non_provider_slash_models(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "siliconflow",
            "LLM_SILICONFLOW_PROTOCOL": "openai",
            "LLM_SILICONFLOW_BASE_URL": "https://api.siliconflow.cn/v1",
            "LLM_SILICONFLOW_API_KEY": "sk-test-value",
            "LLM_SILICONFLOW_MODELS": "Qwen/Qwen3-8B,deepseek-ai/DeepSeek-V3",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(
            config.llm_channels[0]["models"],
            ["openai/Qwen/Qwen3-8B", "openai/deepseek-ai/DeepSeek-V3"],
        )

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_alias_prefixed_models_are_canonicalized_once(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "vertex",
            "LLM_VERTEX_PROTOCOL": "vertex_ai",
            "LLM_VERTEX_API_KEY": "sk-test-value",
            "LLM_VERTEX_MODELS": "vertexai/gemini-2.5-flash",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(config.llm_channels[0]["models"], ["vertex_ai/gemini-2.5-flash"])
        self.assertEqual(config.llm_model_list[0]["litellm_params"]["model"], "vertex_ai/gemini-2.5-flash")

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_disabled_channel_is_skipped(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "primary",
            "LLM_PRIMARY_PROTOCOL": "openai",
            "LLM_PRIMARY_ENABLED": "false",
            "LLM_PRIMARY_API_KEY": "sk-test-value",
            "LLM_PRIMARY_MODELS": "gpt-4o-mini",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(config.llm_channels, [])
        self.assertEqual(config.llm_model_list, [])

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_local_ollama_channel_can_skip_api_key(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "local",
            "LLM_LOCAL_PROTOCOL": "ollama",
            "LLM_LOCAL_BASE_URL": "http://127.0.0.1:11434",
            "LLM_LOCAL_API_KEY": "",
            "LLM_LOCAL_MODELS": "llama3.2",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(config.llm_models_source, "llm_channels")
        params = config.llm_model_list[0]["litellm_params"]
        self.assertEqual(params["model"], "ollama/llama3.2")
        self.assertNotIn("api_key", params)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_llm_temperature_falls_back_to_legacy_provider_temperature(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "GEMINI_API_KEY": "secret-key-value",
            "GEMINI_TEMPERATURE": "0.15",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(config.litellm_model, "gemini/gemini-3-flash-preview")
        self.assertAlmostEqual(config.llm_temperature, 0.15)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_llm_temperature_prefers_unified_setting_when_present(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "GEMINI_API_KEY": "secret-key-value",
            "GEMINI_TEMPERATURE": "0.15",
            "LLM_TEMPERATURE": "0.35",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertAlmostEqual(config.llm_temperature, 0.35)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_llm_temperature_falls_back_to_openai_temperature(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "primary",
            "LLM_PRIMARY_PROTOCOL": "openai",
            "LLM_PRIMARY_API_KEY": "sk-test",
            "LLM_PRIMARY_MODELS": "gpt-4o",
            "LITELLM_MODEL": "openai/gpt-4o",
            "OPENAI_TEMPERATURE": "0.42",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertAlmostEqual(config.llm_temperature, 0.42)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_llm_temperature_falls_back_to_any_legacy_when_provider_mismatch(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "primary",
            "LLM_PRIMARY_PROTOCOL": "openai",
            "LLM_PRIMARY_API_KEY": "sk-test",
            "LLM_PRIMARY_MODELS": "gpt-4o",
            "LITELLM_MODEL": "openai/gpt-4o",
            "ANTHROPIC_TEMPERATURE": "0.55",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertAlmostEqual(config.llm_temperature, 0.55)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_llm_temperature_ignores_invalid_value(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "GEMINI_API_KEY": "secret-key-value",
            "LLM_TEMPERATURE": "high",
            "GEMINI_TEMPERATURE": "0.25",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertAlmostEqual(config.llm_temperature, 0.25)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_local_openai_compatible_channel_defaults_to_openai_protocol(self, _mock_parse_yaml, _mock_setup_env) -> None:
        """Localhost channels without explicit protocol should default to openai, not ollama."""
        env = {
            "LLM_CHANNELS": "local",
            "LLM_LOCAL_BASE_URL": "http://127.0.0.1:8000/v1",
            "LLM_LOCAL_API_KEY": "not-needed",
            "LLM_LOCAL_MODELS": "my-model",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        params = config.llm_model_list[0]["litellm_params"]
        self.assertEqual(params["model"], "openai/my-model")
        self.assertEqual(config.llm_channels[0]["protocol"], "openai")
        self.assertNotIn("extra_headers", params)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_global_extra_headers_apply_to_openai_compatible_channel(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_EXTRA_HEADERS": '{"User-Agent":"Mozilla/5.0 test","X-Relay":"global"}',
            "LLM_CHANNELS": "relay",
            "LLM_RELAY_PROTOCOL": "openai",
            "LLM_RELAY_BASE_URL": "https://relay.example.com/v1",
            "LLM_RELAY_API_KEY": "sk-test-value",
            "LLM_RELAY_MODELS": "gpt-4o-mini",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        headers = config.llm_model_list[0]["litellm_params"]["extra_headers"]
        self.assertEqual(headers["User-Agent"], "Mozilla/5.0 test")
        self.assertEqual(headers["X-Relay"], "global")

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_channel_extra_headers_override_global_headers(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_EXTRA_HEADERS": '{"User-Agent":"GlobalUA","X-Relay":"global"}',
            "LLM_CHANNELS": "relay",
            "LLM_RELAY_PROTOCOL": "openai",
            "LLM_RELAY_BASE_URL": "https://relay.example.com/v1",
            "LLM_RELAY_API_KEY": "sk-test-value",
            "LLM_RELAY_MODELS": "gpt-4o-mini",
            "LLM_RELAY_EXTRA_HEADERS": '{"User-Agent":"ChannelUA","X-Channel":"local"}',
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        headers = config.llm_model_list[0]["litellm_params"]["extra_headers"]
        self.assertEqual(headers["User-Agent"], "ChannelUA")
        self.assertEqual(headers["X-Relay"], "global")
        self.assertEqual(headers["X-Channel"], "local")

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_legacy_openai_uses_global_extra_headers(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_EXTRA_HEADERS": '{"User-Agent":"Mozilla/5.0 test"}',
            "OPENAI_API_KEY": "sk-test-value",
            "OPENAI_BASE_URL": "https://relay.example.com/v1",
            "OPENAI_MODEL": "gpt-4o-mini",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        params = config.llm_model_list[0]["litellm_params"]
        self.assertEqual(params["api_base"], "https://relay.example.com/v1")
        self.assertEqual(params["extra_headers"]["User-Agent"], "Mozilla/5.0 test")

        direct_params = extra_litellm_params("openai/gpt-4o-mini", config)
        self.assertEqual(direct_params["api_base"], "https://relay.example.com/v1")
        self.assertEqual(direct_params["extra_headers"]["User-Agent"], "Mozilla/5.0 test")

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_legacy_openai_without_global_headers_keeps_default_official_behavior(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "OPENAI_API_KEY": "sk-test-value",
            "OPENAI_BASE_URL": "https://relay.example.com/v1",
            "OPENAI_MODEL": "gpt-4o-mini",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        params = config.llm_model_list[0]["litellm_params"]
        self.assertNotIn("extra_headers", params)

    @patch("src.config.setup_env")
    def test_litellm_yaml_uses_global_extra_headers_for_openai_models(self, _mock_setup_env) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "litellm.yaml"
            config_path.write_text(
                """
model_list:
  - model_name: relay-model
    litellm_params:
      model: openai/gpt-4o-mini
      api_base: https://relay.example.com/v1
      api_key: os.environ/RELAY_API_KEY
""",
                encoding="utf-8",
            )
            env = {
                "LITELLM_CONFIG": str(config_path),
                "LLM_EXTRA_HEADERS": '{"User-Agent":"GlobalUA","X-Relay":"global"}',
                "RELAY_API_KEY": "sk-test-value",
            }

            with patch.dict(os.environ, env, clear=True):
                config = Config._load_from_env()

        params = config.llm_model_list[0]["litellm_params"]
        self.assertEqual(params["api_key"], "sk-test-value")
        self.assertEqual(params["extra_headers"]["User-Agent"], "GlobalUA")
        self.assertEqual(params["extra_headers"]["X-Relay"], "global")

    @patch("src.config.setup_env")
    def test_litellm_yaml_extra_headers_override_global_headers(self, _mock_setup_env) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "litellm.yaml"
            config_path.write_text(
                """
model_list:
  - model_name: relay-model
    litellm_params:
      model: openai/gpt-4o-mini
      api_base: https://relay.example.com/v1
      api_key: sk-test-value
      extra_headers:
        User-Agent: YamlUA
        X-Yaml: local
""",
                encoding="utf-8",
            )
            env = {
                "LITELLM_CONFIG": str(config_path),
                "LLM_EXTRA_HEADERS": '{"User-Agent":"GlobalUA","X-Relay":"global"}',
            }

            with patch.dict(os.environ, env, clear=True):
                config = Config._load_from_env()

        params = config.llm_model_list[0]["litellm_params"]
        self.assertEqual(params["extra_headers"]["User-Agent"], "YamlUA")
        self.assertEqual(params["extra_headers"]["X-Relay"], "global")
        self.assertEqual(params["extra_headers"]["X-Yaml"], "local")

    @patch("src.config.setup_env")
    def test_litellm_yaml_does_not_apply_global_headers_to_non_openai_models(self, _mock_setup_env) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "litellm.yaml"
            config_path.write_text(
                """
model_list:
  - model_name: gemini-model
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: sk-test-value
""",
                encoding="utf-8",
            )
            env = {
                "LITELLM_CONFIG": str(config_path),
                "LLM_EXTRA_HEADERS": '{"User-Agent":"GlobalUA"}',
            }

            with patch.dict(os.environ, env, clear=True):
                config = Config._load_from_env()

        params = config.llm_model_list[0]["litellm_params"]
        self.assertNotIn("extra_headers", params)

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_qwen_channel_name_alias_maps_to_openai_protocol(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "qwen",
            "LLM_QWEN_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "LLM_QWEN_API_KEY": "sk-test-value",
            "LLM_QWEN_MODELS": "qwen-plus",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(config.llm_channels[0]["protocol"], "openai")
        self.assertEqual(config.llm_channels[0]["models"], ["openai/qwen-plus"])
        self.assertEqual(config.litellm_model, "openai/qwen-plus")

    @patch("src.config.setup_env")
    @patch.object(Config, "_parse_litellm_yaml", return_value=[])
    def test_channel_order_infers_primary_and_fallback_models(self, _mock_parse_yaml, _mock_setup_env) -> None:
        env = {
            "LLM_CHANNELS": "google,claude,qwen",
            "LLM_GOOGLE_API_KEY": "google-test-key",
            "LLM_GOOGLE_MODELS": "gemini-2.5-flash",
            "LLM_CLAUDE_API_KEY": "claude-test-key",
            "LLM_CLAUDE_MODELS": "claude-3-5-sonnet-20241022",
            "LLM_QWEN_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "LLM_QWEN_API_KEY": "qwen-test-key",
            "LLM_QWEN_MODELS": "qwen-plus",
        }

        with patch.dict(os.environ, env, clear=True):
            config = Config._load_from_env()

        self.assertEqual(config.litellm_model, "gemini/gemini-2.5-flash")
        self.assertEqual(
            config.litellm_fallback_models,
            ["anthropic/claude-3-5-sonnet-20241022", "openai/qwen-plus"],
        )


if __name__ == "__main__":
    unittest.main()
