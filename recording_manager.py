#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
录音管理器
负责扫描录音文件，提取元信息
"""

import os
import re
from datetime import datetime
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from pydub import AudioSegment
import requests
import json
import wave

class Recording:
    def __init__(self, file_path):
        self.file_path = file_path
        self.phone_number = self.extract_phone_number()
        self.call_time = self.extract_call_time()
        self.duration = self.get_duration()
        self.classification = '待确认'  # 重要、不重要、待确认
        self.confirmed = False

    def extract_phone_number(self):
        # 从文件名提取电话号码
        # 假设文件名格式如：录音_13800138000_20231101_120000.m4a
        filename = os.path.basename(self.file_path)
        match = re.search(r'(\d{11}|\d{7,10})', filename)
        return match.group(1) if match else '未知'

    def extract_call_time(self):
        # 从文件名或文件mtime提取时间
        filename = os.path.basename(self.file_path)
        # 尝试从文件名提取，如 _20231101_120000
        match = re.search(r'_(\d{8})_(\d{6})', filename)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            return datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
        else:
            # 使用文件修改时间
            mtime = os.path.getmtime(self.file_path)
            return datetime.fromtimestamp(mtime)

    def get_duration(self):
        try:
            # 对于WAV文件，使用wave模块直接读取
            if self.file_path.lower().endswith('.wav'):
                with wave.open(self.file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    if rate > 0:
                        return frames / float(rate)
            
            # 根据文件扩展名使用对应的mutagen模块
            ext = self.file_path.lower().split('.')[-1]
            
            if ext == 'mp3':
                audio = MP3(self.file_path)
                return audio.info.length
            elif ext in ['m4a', 'mp4']:
                audio = MP4(self.file_path)
                return audio.info.length
            else:
                # 对于其他格式，尝试通用mutagen
                audio_info = MutagenFile(self.file_path)
                if audio_info and hasattr(audio_info, 'info') and hasattr(audio_info.info, 'length'):
                    return float(audio_info.info.length)
            
            # 如果都失败，返回0
            return 0
        except:
            return 0

class RecordingManager:
    def __init__(self):
        self.recordings = []

    def load_recordings(self, folder_path):
        self.recordings = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.m4a', '.mp3', '.amr', '.wav')):
                    file_path = os.path.join(root, file)
                    recording = Recording(file_path)
                    self.recordings.append(recording)
        # 按时间倒序排序
        self.recordings.sort(key=lambda x: x.call_time, reverse=True)

    def classify_recordings(self, contacts, number_classifier):
        for recording in self.recordings:
            # 基于通讯录
            if recording.phone_number in contacts:
                contact = contacts[recording.phone_number]
                if contact['group'] in ['family', 'friend', 'work']:
                    recording.classification = '重要'
                else:
                    recording.classification = '重要'  # 普通联系人仍重要
            else:
                # 基于号码标记
                number_type = number_classifier.classify_number(recording.phone_number)
                if number_type in ['快递', '外卖', '推销']:
                    recording.classification = '不重要'
                elif number_type == '服务':
                    recording.classification = '待确认'
                else:
                    # 规则判断
                    if recording.duration < 10:
                        recording.classification = '不重要'
                    else:
                        recording.classification = '待确认'