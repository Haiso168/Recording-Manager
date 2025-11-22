# 贡献指南

感谢您对通话录音整理工具项目的兴趣！我们欢迎各种形式的贡献。

## 🚀 快速开始

### 开发环境设置

1. **Fork 项目**
   - 点击右上角的 "Fork" 按钮

2. **克隆到本地**
```bash
git clone https://github.com/your-username/recording-manager.git
cd recording-manager
```

3. **创建虚拟环境**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

4. **安装依赖**
```bash
pip install -r requirements.txt
```

5. **运行程序**
```bash
python main.py
```

## 🐛 报告问题

在使用过程中发现问题？请：

1. 检查 [Issues](../../issues) 页面是否已有类似问题
2. 如果没有，创建一个新的 Issue
3. 提供详细的：
   - 问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 系统信息（Windows版本、Python版本等）

## 💡 功能建议

有好的想法？欢迎提出功能建议：

1. 检查是否已有类似建议
2. 创建 Feature Request Issue
3. 详细描述功能需求和使用场景

## 🔧 代码贡献

### 开发流程

1. **创建分支**
```bash
git checkout -b feature/your-feature-name
# 或者
git checkout -b fix/your-bug-fix
```

2. **编写代码**
   - 遵循现有的代码风格
   - 添加必要的注释
   - 确保代码可读性

3. **测试**
   - 运行现有功能确保没有破坏
   - 测试新功能是否正常工作

4. **提交代码**
```bash
git add .
git commit -m "feat: 添加新功能"  # 或 "fix: 修复bug"
```

5. **推送分支**
```bash
git push origin feature/your-feature-name
```

6. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 填写详细描述
   - 等待审查

### 代码规范

- 使用有意义的变量和函数名
- 添加必要的注释
- 遵循 PEP 8 代码风格
- 提交信息使用规范格式：
  - `feat: 新功能`
  - `fix: 修复bug`
  - `docs: 文档更新`
  - `style: 代码格式`
  - `refactor: 重构`
  - `test: 测试`
  - `chore: 杂项`

### 测试

在提交代码前，请确保：

1. 程序能正常启动
2. 基本功能正常工作
3. 没有明显的错误或警告

## 📝 文档贡献

- 更新 README.md
- 改进代码注释
- 添加使用示例
- 翻译文档

## 🎯 行为准则

- 保持友好和尊重
- 提供建设性的反馈
- 遵守开源社区规范

## 📞 联系方式

- 项目维护者: [您的邮箱]
- 项目讨论: [GitHub Discussions]

感谢您的贡献！🎉