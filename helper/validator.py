# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     _validators
   Description :   定义proxy验证方法
   Author :        JHao
   date：          2021/5/25
-------------------------------------------------
   Change Activity:
                   2023/03/10: 支持带用户认证的代理格式 username:password@ip:port
                   2026/08/29: 新增 contentValidator 伪造代理内容检测
                   2026/08/29: 注释停用 httpTimeOutValidator（连通性由 contentValidator 覆盖）
                   2026/09/05: contentValidator 区分伪造(返回"FAKE")与网络失败(返回False)
-------------------------------------------------
"""
__author__ = 'JHao'

import re
from requests import head, get
from util.six import withMetaclass
from util.singleton import Singleton
from handler.configHandler import ConfigHandler

conf = ConfigHandler()

HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
          'Accept': '*/*',
          'Connection': 'keep-alive',
          'Accept-Language': 'zh-CN,zh;q=0.8'}

IP_REGEX = re.compile(r"(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}")


class ProxyValidator(withMetaclass(Singleton)):
    pre_validator = []
    http_validator = []
    https_validator = []

    @classmethod
    def addPreValidator(cls, func):
        cls.pre_validator.append(func)
        return func

    @classmethod
    def addHttpValidator(cls, func):
        cls.http_validator.append(func)
        return func

    @classmethod
    def addHttpsValidator(cls, func):
        cls.https_validator.append(func)
        return func


@ProxyValidator.addPreValidator
def formatValidator(proxy):
    """检查代理格式"""
    return True if IP_REGEX.fullmatch(proxy) else False


# 连通性检测停用: contentValidator 能拿到 baidu 真实 301 响应体即证明代理可用,
# 无需再单独请求 httpbin.org（其不稳定, 故障时会把可用代理全部误杀）。
# 如需恢复检测, 取消下面装饰器的注释即可
# @ProxyValidator.addHttpValidator
def httpTimeOutValidator(proxy):
    """ http检测超时 """

    proxies = {"http": "http://{proxy}".format(proxy=proxy), "https": "https://{proxy}".format(proxy=proxy)}

    try:
        r = head(conf.httpUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False


@ProxyValidator.addHttpsValidator
def httpsTimeOutValidator(proxy):
    """https检测超时"""

    proxies = {"http": "http://{proxy}".format(proxy=proxy), "https": "https://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpsUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout, verify=False)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False


@ProxyValidator.addHttpValidator
def customValidatorExample(proxy):
    """自定义validator函数，校验代理是否可用, 返回True/False"""
    return True


@ProxyValidator.addHttpValidator
def contentValidator(proxy):
    """伪造代理检测: 部分假代理对任何请求都返回200, 仅靠状态码无法识别。
    通过代理 GET CHECK_URL (http://baidu.com, 不跟随重定向), 真实代理会拿到
    baidu 的 301 页面, 其 body 携带 CHECK_KEYWORD 特征; 响应不含该特征即为假代理"""
    proxies = {"http": "http://{proxy}".format(proxy=proxy), "https": "https://{proxy}".format(proxy=proxy)}

    try:
        # 不跟随重定向: http://baidu.com 的 301 响应 body 才携带特征关键字, 跟随后的首页没有
        r = get(conf.checkUrl, headers=HEADER, proxies=proxies,
                timeout=conf.verifyTimeout, allow_redirects=False)
        # 能拿到响应但内容不符 => 伪造/劫持代理, 与超时等网络型失败区分开
        return "FAKE" if conf.checkKeyword not in r.text else True
    except Exception as e:
        return False
