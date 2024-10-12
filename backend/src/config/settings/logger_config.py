import pathlib

from loguru import logger

log_path = pathlib.Path(__file__).resolve().parents[3] / "app.log"
logger.add(str(log_path), rotation="500 MB", retention="10 days", backtrace=True, diagnose=True)
