# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     ip89.py
   Description :   89免费代理代理源
   Author :        JHao
   date：          2026/5/31
-------------------------------------------------
   Change Activity:
                   2026/05/31:
                   2026/08/30: 改用 tqdl 提取接口(原 index_1.html 静态页数据停更, 录取时间停在数月前)
-------------------------------------------------
"""
__author__ = 'JHao'

import re

from fetcher.baseFetcher import BaseFetcher
from util.webRequest import WebRequest


class Ip89Fetcher(BaseFetcher):
    """89免费代理 https://www.89ip.cn/"""

    name = "ip89"
    url = "https://www.89ip.cn/"

    def fetch(self):
        # tqdl 提取接口返回与列表页相同的表格, 数据滚动更新; 服务端每页固定返回 40 条
        r = WebRequest().get("https://www.89ip.cn/tqdl/?api=1&num=100", timeout=10)
        proxies = re.findall(
            r'<td.*?>[\s\S]*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\s\S]*?</td>[\s\S]*?<td.*?>[\s\S]*?(\d+)[\s\S]*?</td>',
            r.text)
        for proxy in proxies:
            yield ':'.join(proxy)


if __name__ == '__main__':
    for proxy in Ip89Fetcher().fetch():
        print(proxy)