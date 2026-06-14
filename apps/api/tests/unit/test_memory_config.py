from app.core.config import Settings


def test_memory_config_defaults():
    settings = Settings()
    assert settings.memory_enabled is True
    assert settings.memory_short_term_enabled is True
    assert settings.memory_long_term_enabled is True
    assert settings.memory_long_term_top_k == 5
    assert settings.memory_min_score == 0.35
    assert settings.max_context_tokens == 8192
    assert settings.reserve_for_reply == 1024
    assert settings.summary_trigger_tokens == 4096
    assert settings.summary_increment_tokens == 1024
    assert settings.summary_cooldown_seconds == 300
