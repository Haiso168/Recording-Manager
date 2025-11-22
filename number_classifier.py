#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
号码分类器
基于本地数据库识别号码类型
"""

class NumberClassifier:
    def __init__(self):
        # 本地号码数据库
        self.number_db = {
            '快递': ['95338', '95546', '4008', '4009'],
            '外卖': ['1010', '4000'],
            '推销': ['170', '171', '1010'],
            '银行': ['955', '400'],
            '服务': ['400', '800']
        }

    def classify_number(self, phone_number):
        # 简化版：检查前缀
        for category, prefixes in self.number_db.items():
            for prefix in prefixes:
                if phone_number.startswith(prefix):
                    return category
        return '未知'