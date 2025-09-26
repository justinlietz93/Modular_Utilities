import logging
from io import StringIO

from code_crawler.domain.configuration import PrivacySettings
from code_crawler.shared.logging import configure_logger


def test_configure_logger_redacts_tokens() -> None:
    stream = StringIO()
    privacy = PrivacySettings(redaction_patterns=[r"secret"])
    logger = configure_logger(privacy)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logger.handlers[0].formatter)
    logger.addHandler(handler)
    logger.info("api secret value")
    output = stream.getvalue()
    assert "[REDACTED]" in output
