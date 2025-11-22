# 📞 通话录音整理工具

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

一个强大的通话录音文件整理工具，支持批量导入、自动智能分类、播放管理和文件清理等功能。

[English](README.md) | [中文](README_CN.md)

</div>

## ✨ 功能特性

### 🎯 核心功能
- **批量导入**：支持同时导入多个录音文件
- **智能分类**：基于通讯录和号码特征自动分类
- **音频播放**：内置播放器，支持快进快退
- **文件管理**：安全删除不需要的录音文件
- **数据导出**：导出整理结果为JSON格式

### 🎵 支持格式
- MP3 (.mp3)
- M4A (.m4a)
- AMR (.amr)
- WAV (.wav)

### 🤖 智能分类规则
- **重要**：通讯录中的联系人
- **不重要**：快递、外卖、推销等服务号码；时长小于10秒的录音
- **待确认**：其他未分类的录音

## 🚀 快速开始

### 方法一：直接使用（推荐）

1. 下载最新版本的可执行文件
2. 双击运行 `启动程序.bat` 或 `dist/main.exe`
3. 开始使用！

### 方法二：开发者模式

#### 环境要求
- Python 3.8+
- Windows 10+

#### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/recording-manager.git
cd recording-manager
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行程序**
```bash
python main.py
```

## 📖 使用指南

### 1. 导入通讯录
- 点击 **"导入通讯录"** 按钮
- 选择 `.vcf` 格式的通讯录文件
- 系统会自动解析联系人信息

### 2. 导入录音文件
- 点击 **"导入录音"** 按钮
- 选择包含录音文件的文件夹
- 支持递归扫描子文件夹

### 3. 智能分类
系统会自动对录音进行分类：
- 左侧显示所有录音
- 中间显示重要/不重要分类
- 右侧显示待删除区

### 4. 手动确认
- 双击分类区域的项目进行确认
- 确认后录音会移至待删除区

### 5. 播放录音
- 双击任意录音项目即可播放
- 支持播放/暂停、快进快退
- 显示当前播放信息

### 6. 批量删除
- 选中待删除区的录音
- 点击 **"确认删除选中录音"** 按钮
- 支持批量操作

## 📁 项目结构

```
recording-manager/
├── main.py                 # 主程序入口
├── recording_manager.py    # 录音管理核心逻辑
├── contact_importer.py     # 通讯录导入模块
├── number_classifier.py    # 号码分类模块
├── requirements.txt        # Python依赖
├── ico/                    # 图标文件
├── dist/                   # 可执行文件（打包后）
├── 启动程序.bat           # 启动脚本
└── README.md              # 项目说明
```

## 🛠️ 技术栈

- **GUI框架**: PyQt5
- **音频处理**: mutagen, pydub
- **数据处理**: Python标准库
- **打包工具**: PyInstaller

## 📋 系统要求

- **操作系统**: Windows 10/11
- **内存**: 至少2GB可用内存
- **存储**: 100MB可用磁盘空间
- **音频**: Windows音频设备（用于播放录音）

## ⚠️ 注意事项

- **备份重要数据**：删除操作不可逆，请先备份重要录音
- **音频设备**：播放功能需要系统音频设备支持
- **文件权限**：确保对录音文件有读取/删除权限
- **大文件处理**：大量录音文件可能需要较长时间处理

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

详细的贡献指南请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

### 快速开始
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙋‍♂️ 联系我们

- 项目维护者: [Your Name]
- 项目主页: https://github.com/your-username/recording-manager
- 问题反馈: [创建Issue](https://github.com/your-username/recording-manager/issues)

## 📊 版本历史

详细的版本更新记录请查看 [CHANGELOG.md](CHANGELOG.md)

### v1.0.0 (2024-11-XX)
- ✅ 初始版本发布
- ✅ 支持批量导入和智能分类
- ✅ 内置音频播放器
- ✅ 文件管理和导出功能

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐ Star！**

Made with ❤️ by [Your Name]

</div>