from browser_agent.logging_utils import get_logger, LOGGER_NAME
import logging


def test_get_logger_default_name():
    logger = get_logger()
    assert logger.name == LOGGER_NAME


def test_get_logger_custom_name():
    logger = get_logger("custom.name")
    assert logger.name == "custom.name"


def test_get_logger_has_handler():
    logger = get_logger("test.logger")
    assert len(logger.handlers) > 0


def test_get_logger_level():
    logger = get_logger("test.level")
    assert logger.level == logging.INFO
