"""
========================================
Task Cache - 任务状态缓存模块
========================================
功能: 缓存最近的任务状态检查结果，避免重复调用AI
 作者: CuteCuteYu
"""

import logging
import time

logger = logging.getLogger(__name__)

# 缓存字典
_task_cache: dict[str, tuple[float, tuple[bool, str]]] = {}
# 缓存超时时间（秒）
_CACHE_TIMEOUT = 30


def get_cached(cache_key: str) -> tuple[bool, str] | None:
    """
    获取缓存的任务检查结果

    参数:
        cache_key: 缓存键

    返回:
        缓存结果 (是否完成, 下一步指令)，未命中或过期返回 None
    """
    cached = _task_cache.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TIMEOUT:
        logger.debug("使用缓存结果")
        return cached[1]
    return None


def set_cached(cache_key: str, result: tuple[bool, str]):
    """写入缓存并清理过期条目"""
    _task_cache[cache_key] = (time.time(), result)
    clean_old_cache(time.time())


def clean_old_cache(current_time: float):
    """
    清理过期缓存

    定期清理超过超时时间的缓存条目

    参数:
        current_time: 当前时间戳
    """
    expired_keys = [
        key
        for key, (cache_time, _) in _task_cache.items()
        if current_time - cache_time > _CACHE_TIMEOUT
    ]
    for key in expired_keys:
        del _task_cache[key]
    if expired_keys:
        logger.debug("清理了 %d 个过期缓存", len(expired_keys))