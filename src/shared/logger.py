import logging
import settings

handlers = [
  # (logging.FileHandler(settings.LOGGING_PATH), logging.DEBUG),
  (logging.StreamHandler(), logging.DEBUG),
]

def init_logger():
  log_formatter = logging.Formatter("%(asctime)s [%(levelname)-8.8s] %(message)s") # removed [%(threadName)-12.12s]
  main_logger = logging.getLogger()
  main_logger.setLevel(logging.DEBUG)

  for handler, level in handlers:
    handler.setFormatter(log_formatter)
    handler.setLevel(level)
    main_logger.addHandler(handler)
