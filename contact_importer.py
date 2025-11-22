#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯录导入器
解析.vcf文件
"""

import vobject

class ContactImporter:
    def __init__(self):
        self.contacts = {}  # phone -> {'name': name, 'group': group}

    def import_vcf(self, vcf_path):
        self.contacts = {}
        with open(vcf_path, 'r', encoding='utf-8') as f:
            vcf_data = f.read()
        
        for vcard in vobject.readComponents(vcf_data):
            if vcard.name == 'VCARD':
                name = ''
                phones = []
                groups = []
                
                if hasattr(vcard, 'fn'):
                    name = vcard.fn.value
                
                if hasattr(vcard, 'tel_list'):
                    for tel in vcard.tel_list:
                        phones.append(tel.value.replace(' ', '').replace('-', ''))
                
                if hasattr(vcard, 'categories'):
                    groups = vcard.categories.value
                
                group = groups[0] if groups else ''
                
                for phone in phones:
                    self.contacts[phone] = {'name': name, 'group': group.lower()}