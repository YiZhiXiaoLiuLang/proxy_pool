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
                   2026/08/30: 改用 api.89ip.cn 批量提取接口(原 index_1.html 静态页数据停更, 录取时间停在数月前)
-------------------------------------------------
"""
__author__ = 'JHao'

from fetcher.baseFetcher import BaseFetcher
from util.webRequest import WebRequest


class Ip89Fetcher(BaseFetcher):
    """89免费代理 https://www.89ip.cn/"""

    name = "ip89"
    url = "https://www.89ip.cn/"

    def fetch(self):
        # 批量提取接口: 响应是混着广告 HTML 的纯文本 ip:port 列表, 用基类方法提取
        r = WebRequest().get(
            "http://api.89ip.cn/tqdl.html?api=1&num=6000&port=&address=&isp=", timeout=10)
        proxies = self.parseProxiesFromText(r.text)
        yield from self.yieldUniqueProxies(proxies)


if __name__ == '__main__':
    for proxy in Ip89Fetcher().fetch():
        print(proxy)