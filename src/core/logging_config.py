import logging


def setup_logging() -> None:
    """配置统一日志格式，便于线上排障与链路追踪。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
