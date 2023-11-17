from logging.config import dictConfig

from .config import DevConfig, config


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    # "format": "%(name)s:%(lineno)d - %(message)s",
                    "format": "%(asctime)s %(levelname)s %(name)s - %(funcName)s - %(lineno)d: %(message)s",
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    # "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
                    "format": "%(asctime)s %(levelname)s %(name)s - %(funcName)s - %(lineno)d: %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "storeapi.log",
                    # 1MB
                    "maxBytes": 1024 * 1024,
                    # 2 MB in total,
                    "backupCount": 2,
                    # best and more compact for english
                    "encoding": "utf8",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
                # root is the parent of all
                # storeapi.routers.post
                "storeapi": {
                    "handlers": ["default", "rotating_file"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    # root is out
                    # we do not want to use it in dev
                    "propagate": False,
                },
                "databases": {"handlers": ["default"], "level": "WARNING"},
                "aiosqlite": {"handlers": ["default"], "level": "WARNING"},
            },
        }
    )
