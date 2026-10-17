from src.utils.helpers import clamp, safe_float
from src.utils.logger import get_logger


def test_clamp_upper_limit():
    assert clamp(150) == 100


def test_clamp_lower_limit():
    assert clamp(-10) == 0


def test_clamp_normal_value():
    assert clamp(50) == 50


def test_safe_float():
    assert safe_float("25.5") == 25.5


def test_safe_float_invalid():
    assert safe_float("invalid", default=10.0) == 10.0


def test_logger():
    logger = get_logger("test_logger")
    assert logger is not None