from config.settings import settings
from config.thresholds import validate_thresholds


def test_settings():

    assert settings.app_name == "Z-Sentinel"
    assert settings.model_dir.exists()


def test_thresholds():

    validate_thresholds()