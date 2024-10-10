import sys
from loguru import logger

logger.remove()
logger.add(
    sink=sys.stdout, 
    format=(
        "<b>Hot Pixel</b> | <white>{time:HH:mm:ss DD.MM}</white>"
        " | <red>LINE:{line: <7}</red>"
        " | <level>{level: <8}</level>"
        " | <white><i>{message}</i></white>"
    ),
    colorize=True,
    level="DEBUG"
)
logger.add(
    sink="logs/hot_pixel_bot.log",
    format=(
        "{time:HH:mm:ss DD.MM} | {level: <8} | {function: <15}  | LINE:{line: <7} | {message}"
    ),
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
    enqueue=True
)
logger = logger.opt(colors=True)

