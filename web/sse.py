"""
========================================
SSE - Server-Sent Events 支撑模块
========================================
功能: 提供 SSE 报文格式化和多客户端事件广播
每个连接的客户端持有独立队列，事件按连接 fan-out，
避免单一 Queue 被多个客户端"抢"走事件
 作者: CuteCuteYu
"""

import asyncio
import json

# 单个订阅者队列上限，超过后丢弃旧事件避免内存无限增长
_SUBSCRIBER_QUEUE_SIZE = 100


def sse_format(payload: dict) -> str:
    """
    将字典格式化为 SSE 数据帧

    参数:
        payload: 要序列化为 JSON 的事件数据

    返回:
        "data: {...}\\n\\n" 格式的字符串
    """
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class EventBroadcaster:
    """
    事件广播器

    维护一组订阅者队列，publish 时将事件复制给所有订阅者。
    每个队列有界，慢消费者只丢自己的旧事件，不影响其他客户端。
    """

    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        """
        订阅事件流

        返回:
            该连接专属的 asyncio.Queue
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=_SUBSCRIBER_QUEUE_SIZE)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """取消订阅（连接断开时调用）"""
        self._subscribers.discard(queue)

    def publish(self, event: dict):
        """
        向所有订阅者广播事件

        参数:
            event: 事件数据字典
        """
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # 队列满时丢弃最旧事件，保住最新事件的时效性
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass
