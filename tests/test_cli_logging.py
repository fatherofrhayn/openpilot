from logging.handlers import RotatingFileHandler
from fork_manager.cli import file_handler, root_logger


def test_file_handler_present_and_configured():
    # Ensure the rotating file handler is registered
    handlers = root_logger.handlers
    rhandlers = [h for h in handlers if isinstance(h, RotatingFileHandler)]
    assert rhandlers, "RotatingFileHandler not found on root logger"
    handler = rhandlers[0]
    # Verify rotation parameters
    assert handler.maxBytes == 5 * 1024 * 1024
    assert handler.backupCount == 3


def test_file_handler_and_module_file_handler_same():
    # The module-level file_handler should match one of the root logger handlers
    assert isinstance(file_handler, RotatingFileHandler)
    assert file_handler in root_logger.handlers
