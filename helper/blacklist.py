# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     blacklist
   Description :   验活失败代理黑名单与连续失败计时(进程内)
   Author :        JHao
   date：          2026/9/5
-------------------------------------------------
   Change Activity:
                   2026/09/05:
-------------------------------------------------
"""
__author__ = 'JHao'

import time
from threading import Lock

# 网络型失败(超时/连接失败等)拉黑时长: 60分钟
BLACKLIST_TIME_NORMAL = 60 * 60

# 伪造代理(可达但baidu响应内容不符)拉黑时长: 120分钟
BLACKLIST_TIME_FAKE = 120 * 60

# 池内代理连续失败满该时长才作废: 5分钟
FAIL_EXPIRE_TIME = 5 * 60


class FailBlacklist(object):
    """失败代理黑名单, 进程内内存实现, 服务重启后自动清空"""

    def __init__(self):
        self._lock = Lock()
        self._blacklist = {}   # proxy_str -> 拉黑截止时间戳
        self._fail_since = {}  # proxy_str -> 池内首次失败时间戳(连续失败计时)

    def add(self, proxy, fake=False):
        """
        拉黑代理
        Args:
            proxy: 代理 ip:port
            fake: True -> 伪造代理拉黑120分钟; False -> 网络型失败拉黑60分钟
        """
        duration = BLACKLIST_TIME_FAKE if fake else BLACKLIST_TIME_NORMAL
        with self._lock:
            self._blacklist[proxy] = time.time() + duration
            self._fail_since.pop(proxy, None)

    def isBlacklisted(self, proxy):
        """是否处于拉黑期内, 过期条目惰性清理"""
        with self._lock:
            expire = self._blacklist.get(proxy)
            if expire is None:
                return False
            if time.time() >= expire:
                del self._blacklist[proxy]
                return False
            return True

    def markFail(self, proxy):
        """
        记录池内代理一次失败, 返回连续失败时长(秒)
        """
        now = time.time()
        with self._lock:
            first = self._fail_since.setdefault(proxy, now)
            return now - first

    def clearFail(self, proxy):
        """清除连续失败计时(检测通过时调用)"""
        with self._lock:
            self._fail_since.pop(proxy, None)


fail_blacklist = FailBlacklist()
