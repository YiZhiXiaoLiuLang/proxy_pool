# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testValidator.py
   Description :   formatValidator正则测试
   Author :        JHao
   date：          2026/5/28
-------------------------------------------------
   Change Activity:
                   2026/05/28:
                   2026/08/29: 新增 contentValidator 伪造代理检测测试
-------------------------------------------------
"""
__author__ = 'JHao'

import re
import pytest
from unittest.mock import patch, MagicMock

# 直接导入 IP_REGEX 和 formatValidator，不导入整个 validator 模块（避免模块级副作用）
from helper.validator import (IP_REGEX, formatValidator, httpTimeOutValidator,
                              httpsTimeOutValidator, contentValidator, customValidatorExample)


class TestIPRegex:

    @pytest.mark.parametrize("proxy", [
        "1.2.3.4:8080",
        "192.168.1.1:3128",
        "10.0.0.1:80",
        "255.255.255.255:65535",
        "0.0.0.0:1",
        "1.2.3.4:99999",   # regex 不校验端口范围
        "999.1.1.1:80",    # regex 不校验 IP 范围
        "user:pass@1.2.3.4:8080",
        "admin:secret@192.168.1.1:443",
    ])
    def test_valid_proxy_format(self, proxy):
        assert IP_REGEX.fullmatch(proxy) is not None, f"应匹配: {proxy}"

    @pytest.mark.parametrize("proxy", [
        "",
        "abc",
        "1.2.3.4",
        "1.2.3.4:",
        ":8080",
        "1.2.3.4:abc",
        "1.2.3.4:8080:extra",
        "host:8080",
    ])
    def test_invalid_proxy_format(self, proxy):
        assert IP_REGEX.fullmatch(proxy) is None, f"不应匹配: {proxy}"


class TestFormatValidator:

    @pytest.mark.parametrize("proxy", [
        "1.2.3.4:8080",
        "192.168.1.1:3128",
        "user:pass@10.0.0.1:80",
    ])
    def test_valid_returns_true(self, proxy):
        assert formatValidator(proxy) is True

    @pytest.mark.parametrize("proxy", [
        "",
        "abc",
        "1.2.3.4",
    ])
    def test_invalid_returns_false(self, proxy):
        assert formatValidator(proxy) is False


class TestHttpTimeOutValidator:
    """httpTimeOutValidator 测试"""

    @patch("helper.validator.head")
    def test_returns_true_on_200(self, mock_head):
        """status_code=200 -> True"""
        mock_head.return_value = MagicMock(status_code=200)
        assert httpTimeOutValidator("1.2.3.4:8080") is True

    @patch("helper.validator.head")
    def test_returns_false_on_non_200(self, mock_head):
        """status_code=502 -> False"""
        mock_head.return_value = MagicMock(status_code=502)
        assert httpTimeOutValidator("1.2.3.4:8080") is False

    @patch("helper.validator.head")
    def test_returns_false_on_exception(self, mock_head):
        """head() raise Timeout -> False"""
        mock_head.side_effect = TimeoutError("connection timed out")
        assert httpTimeOutValidator("1.2.3.4:8080") is False


class TestHttpsTimeOutValidator:
    """httpsTimeOutValidator 测试"""

    @patch("helper.validator.head")
    def test_returns_true_on_200(self, mock_head):
        """status_code=200 -> True"""
        mock_head.return_value = MagicMock(status_code=200)
        assert httpsTimeOutValidator("1.2.3.4:8080") is True
        # 验证 verify=False 被传递
        call_kwargs = mock_head.call_args
        assert call_kwargs[1]["verify"] is False

    @patch("helper.validator.head")
    def test_returns_false_on_non_200(self, mock_head):
        """status_code=502 -> False"""
        mock_head.return_value = MagicMock(status_code=502)
        assert httpsTimeOutValidator("1.2.3.4:8080") is False

    @patch("helper.validator.head")
    def test_returns_false_on_exception(self, mock_head):
        """head() raise Timeout -> False"""
        mock_head.side_effect = TimeoutError("connection timed out")
        assert httpsTimeOutValidator("1.2.3.4:8080") is False


class TestCustomValidatorExample:
    """customValidatorExample 测试"""

    def test_always_returns_true(self):
        """customValidatorExample 始终返回 True"""
        assert customValidatorExample("1.2.3.4:8080") is True


BAIDU_301_BODY = ('<html><head><title>301 Moved Permanently</title></head>'
                  '<body bgcolor="#FFFFFF">'
                  '<a href="https://www.baidu.com/">Moved Permanently</a>.'
                  '</body></html>')


class TestContentValidator:
    """contentValidator 伪造代理内容检测测试"""

    @patch("helper.validator.get")
    def test_returns_true_on_keyword_hit(self, mock_get):
        """响应 body 包含特征关键字 -> True"""
        mock_get.return_value = MagicMock(status_code=301, text=BAIDU_301_BODY)
        assert contentValidator("1.2.3.4:8080") is True

    @patch("helper.validator.get")
    def test_returns_false_on_200_without_keyword(self, mock_get):
        """响应 200 但 body 不含特征关键字(伪造响应) -> False"""
        mock_get.return_value = MagicMock(status_code=200, text="<html>Welcome</html>")
        assert contentValidator("1.2.3.4:8080") is False

    @patch("helper.validator.get")
    def test_returns_false_on_empty_body(self, mock_get):
        """空 body -> False"""
        mock_get.return_value = MagicMock(status_code=301, text="")
        assert contentValidator("1.2.3.4:8080") is False

    @patch("helper.validator.get")
    def test_no_redirect_followed(self, mock_get):
        """必须不跟随重定向(301 的 body 才带特征, 跟随后没有)"""
        mock_get.return_value = MagicMock(status_code=301, text=BAIDU_301_BODY)
        contentValidator("1.2.3.4:8080")
        assert mock_get.call_args[1]["allow_redirects"] is False

    @patch("helper.validator.get")
    def test_returns_false_on_exception(self, mock_get):
        """get() raise Timeout -> False"""
        mock_get.side_effect = TimeoutError("connection timed out")
        assert contentValidator("1.2.3.4:8080") is False