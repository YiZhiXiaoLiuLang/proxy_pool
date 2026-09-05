# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testBlacklist.py
   Description :   失败代理黑名单测试
   Author :        JHao
   date：          2026/9/5
-------------------------------------------------
   Change Activity:
                   2026/09/05:
-------------------------------------------------
"""
__author__ = 'JHao'

from unittest.mock import patch

from helper.blacklist import FailBlacklist, BLACKLIST_TIME_NORMAL, BLACKLIST_TIME_FAKE


class TestFailBlacklist:

    def test_add_then_blacklisted(self):
        bl = FailBlacklist()
        with patch("helper.blacklist.time") as mock_time:
            mock_time.time.return_value = 1000.0
            bl.add("1.2.3.4:80")
            assert bl.isBlacklisted("1.2.3.4:80") is True
            assert bl.isBlacklisted("5.6.7.8:80") is False

    def test_normal_expiry_60min(self):
        bl = FailBlacklist()
        with patch("helper.blacklist.time") as mock_time:
            mock_time.time.return_value = 1000.0
            bl.add("1.2.3.4:80")
            mock_time.time.return_value = 1000.0 + BLACKLIST_TIME_NORMAL - 1
            assert bl.isBlacklisted("1.2.3.4:80") is True
            mock_time.time.return_value = 1000.0 + BLACKLIST_TIME_NORMAL
            assert bl.isBlacklisted("1.2.3.4:80") is False

    def test_fake_expiry_120min(self):
        bl = FailBlacklist()
        with patch("helper.blacklist.time") as mock_time:
            mock_time.time.return_value = 1000.0
            bl.add("1.2.3.4:80", fake=True)
            mock_time.time.return_value = 1000.0 + BLACKLIST_TIME_NORMAL
            # 普通时长已过期, 伪造仍未过期
            assert bl.isBlacklisted("1.2.3.4:80") is True
            mock_time.time.return_value = 1000.0 + BLACKLIST_TIME_FAKE
            assert bl.isBlacklisted("1.2.3.4:80") is False

    def test_markfail_accumulates(self):
        bl = FailBlacklist()
        with patch("helper.blacklist.time") as mock_time:
            mock_time.time.return_value = 1000.0
            assert bl.markFail("1.2.3.4:80") == 0
            mock_time.time.return_value = 1120.0
            assert bl.markFail("1.2.3.4:80") == 120

    def test_clearfail_resets(self):
        bl = FailBlacklist()
        with patch("helper.blacklist.time") as mock_time:
            mock_time.time.return_value = 1000.0
            bl.markFail("1.2.3.4:80")
            mock_time.time.return_value = 1100.0
            bl.clearFail("1.2.3.4:80")
            assert bl.markFail("1.2.3.4:80") == 0

    def test_add_clears_fail_timer(self):
        bl = FailBlacklist()
        with patch("helper.blacklist.time") as mock_time:
            mock_time.time.return_value = 1000.0
            bl.markFail("1.2.3.4:80")
            mock_time.time.return_value = 1100.0
            bl.add("1.2.3.4:80")
            assert bl.markFail("1.2.3.4:80") == 0
