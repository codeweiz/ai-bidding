import logging.handlers
import os.path


# 设置 logging 环境
def setup_logging(
        log_level="INFO",
        log_file="logs/app.log",
        max_bytes=20 * 1024 * 1024,
        backup_count=10,
        console=True
):
    # 日志存储目录
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志格式
    log_format = (
        "[%(asctime)s] | %(levelname)s %(process)d %(threadName)s %(name)s %(funcName)s:%(lineno)d | %(message)s"
    )

    handlers = []

    # 文件转轮日志
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(file_handler)

    # 控制台日志
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)

    logging.basicConfig(level=log_level, handlers=handlers, force=True)


# 自动执行初始化
setup_logging()
