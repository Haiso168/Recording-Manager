#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通话录音整理工具 PC 版
主程序入口
"""

import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QFileDialog, QSplitter, QGroupBox, QTextEdit, QProgressBar, QSlider, QMenu, QMessageBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

from recording_manager import RecordingManager, Recording
from contact_importer import ContactImporter
from number_classifier import NumberClassifier

class ImportWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, folder_path, recording_manager, contact_importer, number_classifier):
        super().__init__()
        self.folder_path = folder_path
        self.recording_manager = recording_manager
        self.contact_importer = contact_importer
        self.number_classifier = number_classifier

    def run(self):
        # 扫描文件
        audio_files = []
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.lower().endswith(('.m4a', '.mp3', '.amr', '.wav')):
                    audio_files.append(os.path.join(root, file))

        total = len(audio_files)
        if total == 0:
            self.finished.emit()
            return

        # 使用多线程并发处理录音文件
        recordings = []
        completed = 0
        
        def process_file(file_path):
            nonlocal completed
            recording = Recording(file_path)
            completed += 1
            self.progress.emit(int(completed / total * 100))
            return recording

        # 使用线程池，线程数为CPU核心数的2倍
        max_workers = min(os.cpu_count() * 2, total)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(process_file, file_path): file_path for file_path in audio_files}
            
            for future in as_completed(future_to_file):
                recording = future.result()
                recordings.append(recording)

        # 按时间排序
        recordings.sort(key=lambda x: x.call_time, reverse=True)
        self.recording_manager.recordings = recordings

        # 分类
        self.recording_manager.classify_recordings(self.contact_importer.contacts, self.number_classifier)
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recording_manager = RecordingManager()
        self.contact_importer = ContactImporter()
        self.number_classifier = NumberClassifier()
        self.media_player = QMediaPlayer()
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.stateChanged.connect(self.update_playing_status)
        self.media_player.error.connect(self.handle_media_error)
        self.current_recording = None
        # 搜索相关变量
        self.search_highlighted_items = set()  # 高亮的项目
        self.search_confirmed_items = set()    # 确认搜索的项目
        self.init_ui()
        
        # 启动时显示使用说明弹窗
        QTimer.singleShot(500, self.show_help)

    def init_ui(self):
        self.setWindowTitle('通话录音整理工具')
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 顶部：菜单按钮
        top_layout = QHBoxLayout()
        self.import_recordings_btn = QPushButton('导入录音')
        self.import_contacts_btn = QPushButton('导入通讯录')
        self.export_results_btn = QPushButton('导出结果')
        self.help_btn = QPushButton('使用说明')
        self.delete_unimportant_btn = QPushButton('删除不重要录音')
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索号码或联系人...")
        self.search_input.setMaximumWidth(200)  # 限制搜索框宽度
        self.search_input.textChanged.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.confirm_search)

        self.import_recordings_btn.clicked.connect(self.import_recordings)
        self.import_contacts_btn.clicked.connect(self.import_contacts)
        self.export_results_btn.clicked.connect(self.export_results)
        self.help_btn.clicked.connect(self.show_help)

        top_layout.addWidget(self.import_recordings_btn)
        top_layout.addWidget(self.import_contacts_btn)
        top_layout.addWidget(self.export_results_btn)
        top_layout.addWidget(self.help_btn)
        top_layout.addStretch()  # 左侧按钮和右侧搜索框之间的弹性空间
        top_layout.addWidget(QLabel("搜索:"))
        top_layout.addWidget(self.search_input)

        main_layout.addLayout(top_layout)

        # 中间：三列布局
        middle_layout = QHBoxLayout()

        # 左侧：录音时间线列表
        self.recording_list = QTableWidget()
        self.recording_list.setColumnCount(5)
        self.recording_list.setHorizontalHeaderLabels(['时间', '号码', '联系人', '时长', '分类'])
        self.recording_list.setSortingEnabled(True)
        self.recording_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.recording_list.horizontalHeader().setStretchLastSection(False)
        # 设置合理的初始列宽
        self.recording_list.setColumnWidth(0, 130)  # 时间列
        self.recording_list.setColumnWidth(1, 90)   # 号码列
        self.recording_list.setColumnWidth(2, 80)   # 联系人列
        self.recording_list.setColumnWidth(3, 60)   # 时长列
        self.recording_list.setColumnWidth(4, 50)   # 分类列
        self.recording_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recording_list.customContextMenuRequested.connect(self.show_context_menu)

        # 中间：系统分类区
        classification_group = QGroupBox("系统分类")
        classification_layout = QVBoxLayout()
        self.important_list = QTableWidget()
        self.important_list.setColumnCount(4)
        self.important_list.setHorizontalHeaderLabels(['时间', '号码', '联系人', '时长'])
        self.important_list.setSortingEnabled(True)
        self.important_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.important_list.setSelectionMode(QTableWidget.ExtendedSelection)
        self.important_list.horizontalHeader().setStretchLastSection(False)
        # 设置合理的初始列宽
        self.important_list.setColumnWidth(0, 130)  # 时间列
        self.important_list.setColumnWidth(1, 90)   # 号码列
        self.important_list.setColumnWidth(2, 80)   # 联系人列
        self.important_list.setColumnWidth(3, 60)   # 时长列
        
        self.unimportant_list = QTableWidget()
        self.unimportant_list.setColumnCount(4)
        self.unimportant_list.setHorizontalHeaderLabels(['时间', '号码', '联系人', '时长'])
        self.unimportant_list.setSortingEnabled(True)
        self.unimportant_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.unimportant_list.setSelectionMode(QTableWidget.ExtendedSelection)
        self.unimportant_list.horizontalHeader().setStretchLastSection(False)
        # 设置合理的初始列宽
        self.unimportant_list.setColumnWidth(0, 130)  # 时间列
        self.unimportant_list.setColumnWidth(1, 90)   # 号码列
        self.unimportant_list.setColumnWidth(2, 80)   # 联系人列
        self.unimportant_list.setColumnWidth(3, 60)   # 时长列
        self.important_list.cellDoubleClicked.connect(lambda: self.confirm_classification('重要'))
        self.unimportant_list.cellDoubleClicked.connect(lambda: self.confirm_classification('不重要'))
        self.important_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.unimportant_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.important_list.customContextMenuRequested.connect(self.show_context_menu)
        self.unimportant_list.customContextMenuRequested.connect(self.show_context_menu)
        classification_layout.addWidget(QLabel("重要 (★)"))
        classification_layout.addWidget(self.important_list)
        classification_layout.addWidget(QLabel("不重要 (○)"))
        classification_layout.addWidget(self.unimportant_list)
        classification_group.setLayout(classification_layout)

        # 右侧：待删除区
        delete_group = QGroupBox("待删除区")
        delete_layout = QVBoxLayout()
        
        self.delete_list = QTableWidget()
        self.delete_list.setColumnCount(5)
        self.delete_list.setHorizontalHeaderLabels(['时间', '号码', '联系人', '时长', '分类'])
        self.delete_list.setSortingEnabled(True)
        self.delete_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.delete_list.setSelectionMode(QTableWidget.ExtendedSelection)  # 多选
        self.delete_list.horizontalHeader().setStretchLastSection(False)
        # 设置合理的初始列宽
        self.delete_list.setColumnWidth(0, 130)  # 时间列
        self.delete_list.setColumnWidth(1, 90)   # 号码列
        self.delete_list.setColumnWidth(2, 80)   # 联系人列
        self.delete_list.setColumnWidth(3, 60)   # 时长列
        self.delete_list.setColumnWidth(4, 50)   # 分类列
        self.delete_list.cellDoubleClicked.connect(self.undo_delete)
        self.delete_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.delete_list.customContextMenuRequested.connect(self.show_context_menu)
        self.confirm_delete_btn = QPushButton('确认删除选中录音')
        delete_layout.addWidget(self.delete_list)
        delete_layout.addWidget(self.confirm_delete_btn)
        delete_group.setLayout(delete_layout)

        self.confirm_delete_btn.clicked.connect(self.confirm_delete)

        middle_layout.addWidget(self.recording_list)
        middle_layout.addWidget(classification_group)
        middle_layout.addWidget(delete_group)

        main_layout.addLayout(middle_layout)

        # 底部：播放控制
        bottom_layout = QVBoxLayout()

        # 播放控制
        playback_layout = QHBoxLayout()
        self.rewind_btn = QPushButton('⏪')
        self.play_pause_btn = QPushButton('▶️')
        self.fast_forward_btn = QPushButton('⏩')
        self.position_slider = QSlider(Qt.Horizontal)
        self.current_time_label = QLabel('00:00')
        self.total_time_label = QLabel('00:00')

        self.rewind_btn.clicked.connect(self.rewind)
        self.play_pause_btn.clicked.connect(self.play_pause)
        self.fast_forward_btn.clicked.connect(self.fast_forward)
        self.position_slider.sliderMoved.connect(self.set_position)

        playback_layout.addWidget(self.rewind_btn)
        playback_layout.addWidget(self.play_pause_btn)
        playback_layout.addWidget(self.fast_forward_btn)
        playback_layout.addWidget(self.position_slider)
        playback_layout.addWidget(self.current_time_label)
        playback_layout.addWidget(QLabel('/'))
        playback_layout.addWidget(self.total_time_label)

        bottom_layout.addLayout(playback_layout)

        # 加载进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        # 当前播放信息
        self.current_playing_label = QLabel("当前播放：无")
        self.current_playing_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        bottom_layout.addWidget(self.current_playing_label)

        main_layout.addLayout(bottom_layout)

    def import_recordings(self):
        folder = QFileDialog.getExistingDirectory(self, "选择录音文件夹")
        if folder:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.import_worker = ImportWorker(folder, self.recording_manager, self.contact_importer, self.number_classifier)
            self.import_worker.progress.connect(self.progress_bar.setValue)
            self.import_worker.finished.connect(self.on_import_finished)
            self.import_worker.start()

    def on_import_finished(self):
        self.progress_bar.setVisible(False)
        self.update_recording_list()
        self.update_classification_lists()
        self.update_delete_list()

    def import_contacts(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择通讯录文件", "", "VCF files (*.vcf)")
        if file_path:
            self.contact_importer.import_vcf(file_path)
            # 重新分类
            if self.recording_manager.recordings:
                self.recording_manager.classify_recordings(self.contact_importer.contacts, self.number_classifier)
                self.update_recording_list()
                self.update_classification_lists()

    def update_recording_list(self):
        self.recording_list.setRowCount(0)
        for rec in self.recording_manager.recordings:
            row = self.recording_list.rowCount()
            self.recording_list.insertRow(row)
            
            # 时间
            time_item = QTableWidgetItem(rec.call_time.strftime('%Y-%m-%d %H:%M:%S'))
            self.recording_list.setItem(row, 0, time_item)
            
            # 号码
            phone_item = QTableWidgetItem(rec.phone_number)
            self.recording_list.setItem(row, 1, phone_item)
            
            # 联系人
            contact_item = QTableWidgetItem(self.get_contact_name(rec.phone_number))
            self.recording_list.setItem(row, 2, contact_item)
            
            # 时长
            duration_str = f"{int(rec.duration // 3600):02d}:{int((rec.duration % 3600) // 60):02d}:{int(rec.duration % 60):02d}"
            duration_item = QTableWidgetItem(duration_str)
            self.recording_list.setItem(row, 3, duration_item)
            
            # 分类
            classification_item = QTableWidgetItem(rec.classification)
            self.recording_list.setItem(row, 4, classification_item)
        
        # 重新应用搜索高亮
        if self.search_input.text().strip():
            self.perform_search(self.search_input.text())

    def update_classification_lists(self):
        self.important_list.setRowCount(0)
        self.unimportant_list.setRowCount(0)
        for rec in self.recording_manager.recordings:
            if not rec.confirmed:
                contact_name = self.get_contact_name(rec.phone_number)
                duration_str = f"{int(rec.duration // 3600):02d}:{int((rec.duration % 3600) // 60):02d}:{int(rec.duration % 60):02d}"
                
                if rec.classification == '重要':
                    row = self.important_list.rowCount()
                    self.important_list.insertRow(row)
                    
                    time_item = QTableWidgetItem(rec.call_time.strftime('%Y-%m-%d %H:%M:%S'))
                    self.important_list.setItem(row, 0, time_item)
                    
                    phone_item = QTableWidgetItem(rec.phone_number)
                    self.important_list.setItem(row, 1, phone_item)
                    
                    contact_item = QTableWidgetItem(contact_name)
                    self.important_list.setItem(row, 2, contact_item)
                    
                    duration_item = QTableWidgetItem(duration_str)
                    self.important_list.setItem(row, 3, duration_item)
                    
                elif rec.classification == '不重要':
                    row = self.unimportant_list.rowCount()
                    self.unimportant_list.insertRow(row)
                    
                    time_item = QTableWidgetItem(rec.call_time.strftime('%Y-%m-%d %H:%M:%S'))
                    self.unimportant_list.setItem(row, 0, time_item)
                    
                    phone_item = QTableWidgetItem(rec.phone_number)
                    self.unimportant_list.setItem(row, 1, phone_item)
                    
                    contact_item = QTableWidgetItem(contact_name)
                    self.unimportant_list.setItem(row, 2, contact_item)
                    
                    duration_item = QTableWidgetItem(duration_str)
                    self.unimportant_list.setItem(row, 3, duration_item)
        
        # 重新应用搜索高亮
        if self.search_input.text().strip():
            self.perform_search(self.search_input.text())

    def get_contact_name(self, phone):
        if phone in self.contact_importer.contacts:
            return self.contact_importer.contacts[phone]['name']
        return '不在通讯录内'

    def play_recording(self, item):
        # 获取录音路径
        row = self.recording_list.currentRow()
        if row >= 0:
            rec = self.recording_manager.recordings[row]
            self.current_recording = rec

            try:
                # 检查文件是否存在
                if not os.path.exists(rec.file_path):
                    QMessageBox.warning(self, "播放失败", f"音频文件不存在：\n{rec.file_path}")
                    return

                # 设置媒体
                media_url = QUrl.fromLocalFile(rec.file_path)
                self.media_player.setMedia(QMediaContent(media_url))

                # 开始播放
                self.media_player.play()
                self.play_pause_btn.setText('⏸️')

            except Exception as e:
                QMessageBox.warning(self, "播放失败", f"播放过程中发生错误：\n{str(e)}\n\n文件：{rec.file_path}")

    def play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_btn.setText('▶️')
        else:
            self.media_player.play()
            self.play_pause_btn.setText('⏸️')
            # 如果有当前录音，更新显示
            if self.current_recording:
                contact_name = self.get_contact_name(self.current_recording.phone_number)
                self.current_playing_label.setText(f"当前播放：{self.current_recording.call_time.strftime('%Y-%m-%d %H:%M:%S')} | {self.current_recording.phone_number} | {contact_name}")

    def rewind(self):
        current_pos = self.media_player.position()
        self.media_player.setPosition(max(0, current_pos - 10000))  # 10秒

    def fast_forward(self):
        current_pos = self.media_player.position()
        duration = self.media_player.duration()
        self.media_player.setPosition(min(duration, current_pos + 10000))  # 10秒

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_position(self, position):
        self.position_slider.setValue(position)
        self.current_time_label.setText(self.format_time(position))

    def update_duration(self, duration):
        self.position_slider.setMaximum(duration)
        self.total_time_label.setText(self.format_time(duration))

    def update_playing_status(self, state):
        if state == QMediaPlayer.StoppedState:
            self.current_playing_label.setText("当前播放：无")
            self.play_pause_btn.setText('▶️')

    def handle_media_error(self, error):
        error_msg = self.media_player.errorString()
        if error_msg:
            QMessageBox.warning(self, "媒体播放错误", f"播放失败：\n{error_msg}")
        else:
            QMessageBox.warning(self, "媒体播放错误", "播放失败：未知错误")

    def format_time(self, ms):
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def export_results(self):
        # 导出为JSON
        import json
        results = []
        for rec in self.recording_manager.recordings:
            results.append({
                'file_path': rec.file_path,
                'phone_number': rec.phone_number,
                'call_time': rec.call_time.isoformat(),
                'duration': rec.duration,
                'classification': rec.classification
            })
        with open('recording_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def confirm_classification(self, classification):
        # 获取当前选中的rows
        sender = self.sender()
        selected_rows = set()
        if sender == self.important_list:
            selected_rows = set(index.row() for index in self.important_list.selectionModel().selectedRows())
        elif sender == self.unimportant_list:
            selected_rows = set(index.row() for index in self.unimportant_list.selectionModel().selectedRows())
        
        for row in selected_rows:
            # 从表格获取数据
            if sender == self.important_list:
                time_str = self.important_list.item(row, 0).text()
                phone = self.important_list.item(row, 1).text()
                contact_name = self.important_list.item(row, 2).text()
            elif sender == self.unimportant_list:
                time_str = self.unimportant_list.item(row, 0).text()
                phone = self.unimportant_list.item(row, 1).text()
                contact_name = self.unimportant_list.item(row, 2).text()
            
            # 找到对应的recording
            for rec in self.recording_manager.recordings:
                if not rec.confirmed and rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    rec.confirmed = True
                    rec.classification = classification
                    break
            
            # 添加到待删除区
            delete_row = self.delete_list.rowCount()
            self.delete_list.insertRow(delete_row)
            
            time_item = QTableWidgetItem(time_str)
            self.delete_list.setItem(delete_row, 0, time_item)
            
            phone_item = QTableWidgetItem(phone)
            self.delete_list.setItem(delete_row, 1, phone_item)
            
            contact_item = QTableWidgetItem(contact_name)
            self.delete_list.setItem(delete_row, 2, contact_item)
            
            # 查找时长
            duration_str = "00:00:00"
            for rec in self.recording_manager.recordings:
                if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    duration_str = f"{int(rec.duration // 3600):02d}:{int((rec.duration % 3600) // 60):02d}:{int(rec.duration % 60):02d}"
                    break
            
            duration_item = QTableWidgetItem(duration_str)
            self.delete_list.setItem(delete_row, 3, duration_item)
            
            classification_item = QTableWidgetItem(classification)
            self.delete_list.setItem(delete_row, 4, classification_item)
            
            # 从原列表移除（需要反向删除以保持索引正确）
        
        # 重新填充原列表以移除选中的行
        self.update_classification_lists()
        
        # 更新录音列表
        self.update_recording_list()

    def undo_delete(self):
        # 从待删除区移出
        row = self.delete_list.currentRow()
        if row < 0:
            return
            
        time_str = self.delete_list.item(row, 0).text()
        phone = self.delete_list.item(row, 1).text()
        contact_name = self.delete_list.item(row, 2).text()
        classification = self.delete_list.item(row, 4).text()
        
        # 找到recording
        for rec in self.recording_manager.recordings:
            if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                rec.confirmed = False
                rec.classification = classification
                break
        
        # 移回分类列表
        duration_str = "00:00:00"
        for rec in self.recording_manager.recordings:
            if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                duration_str = f"{int(rec.duration // 3600):02d}:{int((rec.duration % 3600) // 60):02d}:{int(rec.duration % 60):02d}"
                break
        
        if classification == '重要':
            important_row = self.important_list.rowCount()
            self.important_list.insertRow(important_row)
            
            self.important_list.setItem(important_row, 0, QTableWidgetItem(time_str))
            self.important_list.setItem(important_row, 1, QTableWidgetItem(phone))
            self.important_list.setItem(important_row, 2, QTableWidgetItem(contact_name))
            self.important_list.setItem(important_row, 3, QTableWidgetItem(duration_str))
            
        elif classification == '不重要':
            unimportant_row = self.unimportant_list.rowCount()
            self.unimportant_list.insertRow(unimportant_row)
            
            self.unimportant_list.setItem(unimportant_row, 0, QTableWidgetItem(time_str))
            self.unimportant_list.setItem(unimportant_row, 1, QTableWidgetItem(phone))
            self.unimportant_list.setItem(unimportant_row, 2, QTableWidgetItem(contact_name))
            self.unimportant_list.setItem(unimportant_row, 3, QTableWidgetItem(duration_str))
        
        # 从待删除区移除
        self.delete_list.removeRow(row)
        
        # 更新录音列表
        self.update_recording_list()

    def show_context_menu(self, position):
        # 右键菜单，支持单选和多选操作
        sender = self.sender()
        if isinstance(sender, QTableWidget):
            selected_rows = sender.selectionModel().selectedRows()
            if not selected_rows:
                return
                
            menu = QMenu()
            
            # 播放操作
            if len(selected_rows) == 1:
                play_action = menu.addAction("播放录音")
                play_action.triggered.connect(lambda: self.play_recording_from_context(sender, selected_rows[0]))
            else:
                play_first_action = menu.addAction("播放第一个选中录音")
                play_first_action.triggered.connect(lambda: self.play_selected_recordings(sender, selected_rows))
            
            # 批量移动操作（仅对分类区有效）
            if sender in [self.important_list, self.unimportant_list] and len(selected_rows) > 1:
                menu.addSeparator()
                move_to_delete_action = menu.addAction("批量移至待删除区")
                move_to_delete_action.triggered.connect(lambda: self.batch_confirm_classification(sender, selected_rows))
            
            # 批量删除操作（仅对待删除区有效）
            if sender == self.delete_list and len(selected_rows) > 1:
                menu.addSeparator()
                batch_delete_action = menu.addAction("批量删除选中录音")
                batch_delete_action.triggered.connect(lambda: self.batch_delete_selected(selected_rows))
            
            # 撤销选择操作（仅在删除区显示，支持单选和多选）
            if sender == self.delete_list:
                menu.addSeparator()
                if len(selected_rows) == 1:
                    undo_selection_action = menu.addAction("撤销选择")
                else:
                    undo_selection_action = menu.addAction("批量撤销选择")
                undo_selection_action.triggered.connect(lambda: self.batch_undo_selection(selected_rows))
            
            menu.exec_(sender.mapToGlobal(position))

    def play_recording_from_context(self, table_widget, model_index):
        # 从右键菜单播放录音
        row = model_index.row()
        
        if table_widget == self.recording_list:
            # 录音列表：时间 | 号码 | 联系人 | 时长 | 分类
            time_str = table_widget.item(row, 0).text()
            phone = table_widget.item(row, 1).text()
        elif table_widget in [self.important_list, self.unimportant_list]:
            # 分类区：时间 | 号码 | 联系人 | 时长
            time_str = table_widget.item(row, 0).text()
            phone = table_widget.item(row, 1).text()
        elif table_widget == self.delete_list:
            # 待删除区：时间 | 号码 | 联系人 | 时长 | 分类
            time_str = table_widget.item(row, 0).text()
            phone = table_widget.item(row, 1).text()
        else:
            return
            
        # 查找并播放录音
        for rec in self.recording_manager.recordings:
            if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                self.current_recording = rec
                try:
                    # 检查文件是否存在
                    if not os.path.exists(rec.file_path):
                        QMessageBox.warning(self, "播放失败", f"音频文件不存在：\n{rec.file_path}")
                        return

                    # 设置媒体
                    media_url = QUrl.fromLocalFile(rec.file_path)
                    self.media_player.setMedia(QMediaContent(media_url))

                    # 开始播放
                    self.media_player.play()
                    self.play_pause_btn.setText('⏸️')

                    # 更新播放信息
                    contact_name = self.get_contact_name(rec.phone_number)
                    self.current_playing_label.setText(f"当前播放：{rec.call_time.strftime('%Y-%m-%d %H:%M:%S')} | {rec.phone_number} | {contact_name}")

                except Exception as e:
                    QMessageBox.warning(self, "播放失败", f"播放过程中发生错误：\n{str(e)}\n\n文件：{rec.file_path}")
                break

    def play_selected_recordings(self, table_widget, selected_rows):
        # 播放第一个选中的录音，并取消多选
        if selected_rows:
            self.play_recording_from_context(table_widget, selected_rows[0])
            # 取消多选
            table_widget.clearSelection()

    def batch_confirm_classification(self, sender, selected_rows):
        # 批量移动到待删除区
        classification = '待确认'  # 默认
        if sender == self.important_list:
            classification = '重要'
        elif sender == self.unimportant_list:
            classification = '不重要'
            
        for model_index in selected_rows:
            row = model_index.row()
            # 从表格获取数据
            if sender == self.important_list:
                time_str = self.important_list.item(row, 0).text()
                phone = self.important_list.item(row, 1).text()
                contact_name = self.important_list.item(row, 2).text()
            elif sender == self.unimportant_list:
                time_str = self.unimportant_list.item(row, 0).text()
                phone = self.unimportant_list.item(row, 1).text()
                contact_name = self.unimportant_list.item(row, 2).text()
            
            # 找到对应的recording
            for rec in self.recording_manager.recordings:
                if not rec.confirmed and rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    rec.confirmed = True
                    rec.classification = classification
                    break
            
            # 添加到待删除区
            delete_row = self.delete_list.rowCount()
            self.delete_list.insertRow(delete_row)
            
            self.delete_list.setItem(delete_row, 0, QTableWidgetItem(time_str))
            self.delete_list.setItem(delete_row, 1, QTableWidgetItem(phone))
            self.delete_list.setItem(delete_row, 2, QTableWidgetItem(contact_name))
            
            # 查找时长
            duration_str = "00:00:00"
            for rec in self.recording_manager.recordings:
                if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    duration_str = f"{int(rec.duration // 3600):02d}:{int((rec.duration % 3600) // 60):02d}:{int(rec.duration % 60):02d}"
                    break
            
            self.delete_list.setItem(delete_row, 3, QTableWidgetItem(duration_str))
            self.delete_list.setItem(delete_row, 4, QTableWidgetItem(classification))
        
        # 重新填充原列表以移除选中的行
        self.update_classification_lists()
        
        # 更新录音列表
        self.update_recording_list()

    def batch_delete_selected(self, selected_rows):
        # 批量删除选中的录音
        for model_index in selected_rows:
            row = model_index.row()
            time_str = self.delete_list.item(row, 0).text()
            phone = self.delete_list.item(row, 1).text()
            
            # 找到recording并删除文件
            for rec in self.recording_manager.recordings:
                if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    try:
                        os.remove(rec.file_path)
                    except:
                        pass  # 文件可能已删除
                    break
        
        # 重新更新所有列表
        self.recording_manager.recordings = [rec for rec in self.recording_manager.recordings if os.path.exists(rec.file_path)]
        self.update_recording_list()
        self.update_classification_lists()
        self.update_delete_list()

    def batch_undo_selection(self, selected_rows):
        # 批量撤销选择操作，将录音从待删除区移回原分类区
        for model_index in selected_rows:
            # 直接处理每个选中的行
            row = model_index.row()
            time_str = self.delete_list.item(row, 0).text()
            phone = self.delete_list.item(row, 1).text()
            contact_name = self.delete_list.item(row, 2).text()
            classification = self.delete_list.item(row, 4).text()
            
            # 找到recording
            for rec in self.recording_manager.recordings:
                if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    rec.confirmed = False
                    rec.classification = classification
                    break
            
            # 移回分类列表
            duration_str = "00:00:00"
            for rec in self.recording_manager.recordings:
                if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    duration_str = f"{int(rec.duration // 3600):02d}:{int((rec.duration % 3600) // 60):02d}:{int(rec.duration % 60):02d}"
                    break
            
            if classification == '重要':
                important_row = self.important_list.rowCount()
                self.important_list.insertRow(important_row)
                
                self.important_list.setItem(important_row, 0, QTableWidgetItem(time_str))
                self.important_list.setItem(important_row, 1, QTableWidgetItem(phone))
                self.important_list.setItem(important_row, 2, QTableWidgetItem(contact_name))
                self.important_list.setItem(important_row, 3, QTableWidgetItem(duration_str))
                
            elif classification == '不重要':
                unimportant_row = self.unimportant_list.rowCount()
                self.unimportant_list.insertRow(unimportant_row)
                
                self.unimportant_list.setItem(unimportant_row, 0, QTableWidgetItem(time_str))
                self.unimportant_list.setItem(unimportant_row, 1, QTableWidgetItem(phone))
                self.unimportant_list.setItem(unimportant_row, 2, QTableWidgetItem(contact_name))
                self.unimportant_list.setItem(unimportant_row, 3, QTableWidgetItem(duration_str))
        
        # 重新填充待删除区以移除选中的行
        self.update_delete_list()
        
    def update_delete_list(self):
        # 更新待删除区列表
        self.delete_list.setRowCount(0)
        for rec in self.recording_manager.recordings:
            if rec.confirmed:
                row = self.delete_list.rowCount()
                self.delete_list.insertRow(row)
                
                time_item = QTableWidgetItem(rec.call_time.strftime('%Y-%m-%d %H:%M:%S'))
                self.delete_list.setItem(row, 0, time_item)
                
                phone_item = QTableWidgetItem(rec.phone_number)
                self.delete_list.setItem(row, 1, phone_item)
                
                contact_item = QTableWidgetItem(self.get_contact_name(rec.phone_number))
                self.delete_list.setItem(row, 2, contact_item)
                
                duration_str = f"{int(rec.duration // 3600):02d}:{int((rec.duration % 3600) // 60):02d}:{int(rec.duration % 60):02d}"
                duration_item = QTableWidgetItem(duration_str)
                self.delete_list.setItem(row, 3, duration_item)
                
                classification_item = QTableWidgetItem(rec.classification)
                self.delete_list.setItem(row, 4, classification_item)

    def confirm_delete(self):
        # 如果没有选中任何项，则默认删除待删除区中的所有项目
        selected_rows = self.delete_list.selectionModel().selectedRows()
        if not selected_rows:
            # 删除所有行
            selected_rows = [self.delete_list.model().index(row, 0) for row in range(self.delete_list.rowCount())]

        failed_deletions = []
        for model_index in selected_rows:
            row = model_index.row()
            time_str = self.delete_list.item(row, 0).text()
            phone = self.delete_list.item(row, 1).text()
            
            # 找到recording并删除文件
            for rec in self.recording_manager.recordings:
                if rec.phone_number == phone and rec.call_time.strftime('%Y-%m-%d %H:%M:%S') == time_str:
                    # 如果正在播放此文件，先停止播放以避免 Windows 文件锁定
                    try:
                        if self.current_recording and os.path.abspath(rec.file_path) == os.path.abspath(self.current_recording.file_path):
                            if self.media_player.state() == QMediaPlayer.PlayingState:
                                self.media_player.stop()
                                self.play_pause_btn.setText('▶️')
                    except Exception:
                        pass

                    try:
                        os.remove(rec.file_path)
                    except Exception as e:
                        # 记录删除失败以便提示用户
                        failed_deletions.append((rec.file_path, str(e)))
                    break
        
        # 重新更新所有列表
        self.recording_manager.recordings = [rec for rec in self.recording_manager.recordings if os.path.exists(rec.file_path)]
        self.update_recording_list()
        self.update_classification_lists()
        self.update_delete_list()

        # 提示删除结果
        if failed_deletions:
            # 汇总若干失败项，提示用户其中一些无法删除（常见原因：被占用、权限）
            msg = "以下文件删除失败：\n"
            for fp, err in failed_deletions[:10]:
                msg += f"{fp} -> {err}\n"
            if len(failed_deletions) > 10:
                msg += f"... 另外 {len(failed_deletions)-10} 项失败。\n"
            msg += "请确保这些文件没有被其他程序占用（如正在播放），或手动删除。"
            QMessageBox.warning(self, "删除部分失败", msg)
        else:
            if selected_rows:
                QMessageBox.information(self, "删除完成", "已删除选中的录音（或从待删除区移除）")

    def perform_search(self, text):
        # 即时搜索功能
        search_text = text.lower().strip()
        
        # 清除之前的搜索状态
        self.clear_search_highlights()
        
        if not search_text:
            return
            
        # 在三个列表中搜索匹配项
        search_tables = [self.important_list, self.unimportant_list, self.delete_list]
        
        for table_widget in search_tables:
            for row in range(table_widget.rowCount()):
                phone = table_widget.item(row, 1).text() if table_widget.item(row, 1) else ""
                contact = table_widget.item(row, 2).text() if table_widget.item(row, 2) else ""
                
                # 检查是否匹配（号码或联系人）
                if search_text in phone.lower() or search_text in contact.lower():
                    # 高亮匹配行（黄色背景）
                    for col in range(table_widget.columnCount()):
                        item = table_widget.item(row, col)
                        if item:
                            item.setBackground(Qt.yellow)
                    self.search_highlighted_items.add((table_widget, row))

    def confirm_search(self):
        # 回车键确认搜索，将匹配项字体变为红色
        for table_widget, row in self.search_highlighted_items:
            if row < table_widget.rowCount():
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    if item:
                        item.setForeground(Qt.red)
                self.search_confirmed_items.add((table_widget, row))

    def clear_search_highlights(self):
        # 清除所有搜索高亮和确认状态
        all_tables = [self.important_list, self.unimportant_list, self.delete_list]
        
        for table_widget in all_tables:
            for row in range(table_widget.rowCount()):
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    if item:
                        item.setBackground(Qt.white)  # 恢复默认背景
                        item.setForeground(Qt.black)  # 恢复默认字体颜色
        
        self.search_highlighted_items.clear()
        self.search_confirmed_items.clear()

    def show_help(self):
        # 显示使用说明弹窗
        help_text = """
通话录音整理工具使用说明

基本功能：
1. 导入录音：选择包含录音文件的文件夹，工具会自动扫描并导入支持格式的音频文件（.m4a, .mp3, .amr, .wav）
2. 导入通讯录：导入VCF格式的通讯录文件，用于匹配电话号码和联系人姓名
3. 系统自动分类：根据号码特征和通讯录信息，自动将录音分为"重要"和"不重要"两类

操作说明：
• 双击分类区录音：将录音移动到待删除区
• 右键录音：显示上下文菜单，支持播放、批量操作等
• 搜索功能：在待删除区上方的搜索框中输入号码或联系人姓名，支持实时搜索和回车确认
• 删除录音：选中待删除区录音，点击"确认删除选中录音"按钮

搜索功能：
• 即时搜索：输入字符时实时过滤匹配项（黄色高亮）
• 回车确认：按Enter键将匹配项字体变为红色
• 清空搜索：清空搜索框恢复默认显示

播放控制：
• 使用底部播放控件播放选中的录音
• 支持快进、快退、进度控制

注意事项：
• 删除操作不可逆，请谨慎操作
• 如果录音文件正在播放，删除时会自动停止播放
• 支持多选操作，提高批量处理效率

快捷键：
• Enter：在搜索框中确认搜索结果
• 双击：在分类区快速移动录音到待删除区
        """
        
        QMessageBox.information(self, "使用说明", help_text.strip())

if __name__ == '__main__':
    # 选择并设置应用图标（使用指定的 128.ico）
    def _find_best_icon():
        ico_dir = os.path.join(os.path.dirname(__file__), 'ico')
        icon_path = os.path.join(ico_dir, 'movie_recorder_voice_speaker_mike_icon_128.ico')
        if os.path.isfile(icon_path):
            return icon_path
        return None

    app = QApplication(sys.argv)
    # 设置应用级图标，这通常会影响任务栏和一些系统托盘显示
    icon_path = _find_best_icon()
    if icon_path:
        try:
            app.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

    window = MainWindow()
    # 再次设置窗口图标，确保窗口左上角显示正确图标
    if icon_path:
        try:
            window.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

    window.show()
    sys.exit(app.exec_())