import logging
import time
import functools

def retryable(retries=3, delay=1, rollback_fn=None):
    """
    Decorator to retry a function up to `retries` times with `delay` seconds between attempts.
    On final failure, attempts rollback by calling rollback_fn() if provided, otherwise undo_swap().
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logging.exception(f"Attempt {attempt} for {fn.__name__} failed")
                    if attempt < retries:
                        time.sleep(delay)
                        logging.info(f"Retrying {fn.__name__} (attempt {attempt + 1}/{retries})")
                        continue
                    logging.critical(f"{fn.__name__} failed after {retries} attempts, performing rollback")
                    if rollback_fn:
                        try:
                            rollback_fn(*args, **kwargs)
                        except Exception:
                            logging.exception("Rollback function failed")
                    else:
                        try:
                            # dynamic import to avoid circular dependency
                            from .fork_swap import undo_swap as _undo
                            _undo()
                        except Exception:
                            logging.exception("Rollback (undo_swap) failed")
                    raise
            # Should not reach here
            if last_exception:
                raise last_exception
        return wrapper
    return decorator
