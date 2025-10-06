# 贡献指南

感谢您对 QwenGround 项目的关注！我们欢迎任何形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议：

1. 查看 [Issues](https://github.com/Starryyu77/qwenground/issues) 确认问题是否已被报告
2. 如果没有，创建新的 Issue，并包含：
   - 清晰的标题和描述
   - 复现步骤（如果是 bug）
   - 期望的行为
   - 实际的行为
   - 环境信息（Python版本、CUDA版本、操作系统等）
   - 相关的日志或截图

### 提交代码

1. **Fork 项目**
   ```bash
   # 在 GitHub 上点击 Fork 按钮
   git clone https://github.com/你的用户名/qwenground.git
   cd qwenground
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **进行修改**
   - 保持代码风格一致
   - 添加必要的注释
   - 更新相关文档
   - 添加测试（如果适用）

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加某某功能"
   # 或
   git commit -m "fix: 修复某某问题"
   ```

   提交信息格式：
   - `feat:` 新功能
   - `fix:` 修复bug
   - `docs:` 文档更新
   - `style:` 代码格式（不影响代码运行）
   - `refactor:` 重构
   - `test:` 测试相关
   - `chore:` 构建过程或辅助工具的变动

5. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 描述你的更改
   - 关联相关的 Issue（如果有）

## 📝 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 4 个空格缩进
- 最大行长度 100 字符
- 使用类型提示（Type Hints）

示例：
```python
def process_image(image_path: str, query: str) -> Dict[str, Any]:
    """处理图像并返回结果。
    
    Args:
        image_path: 图像文件路径
        query: 查询文本
        
    Returns:
        包含处理结果的字典
    """
    # 实现代码
    pass
```

### 文档规范

- 所有公共函数/类必须有文档字符串
- 使用 Google 风格的文档字符串
- 保持文档与代码同步更新

## 🧪 测试

在提交代码前，请确保：

1. 代码通过所有现有测试
   ```bash
   python -m pytest tests/
   ```

2. 添加新功能时，添加相应的测试用例

3. 运行代码检查
   ```bash
   # 格式检查
   python scripts/check_deps.py
   ```

## 📚 文档贡献

文档同样重要！您可以：

- 修正文档中的错误
- 添加使用示例
- 翻译文档
- 改进文档结构

## 🔄 开发流程

1. **设置开发环境**
   ```bash
   # 安装开发依赖
   pip install -r requirements.txt
   
   # 安装代码检查工具
   pip install flake8 black mypy
   ```

2. **保持更新**
   ```bash
   # 添加上游仓库
   git remote add upstream https://github.com/Starryyu77/qwenground.git
   
   # 同步最新代码
   git fetch upstream
   git merge upstream/main
   ```

3. **代码审查**
   - 所有 PR 需要至少一位维护者审查
   - 积极回应审查意见
   - 保持 PR 专注于单一目的

## 🌟 成为贡献者

我们认可所有形式的贡献：

- 代码贡献
- 文档改进
- Bug 报告
- 功能建议
- 问题解答
- 宣传推广

所有贡献者将被列入项目的贡献者名单。

## ❓ 需要帮助？

如有任何问题，可以：

- 在 [Discussions](https://github.com/Starryyu77/qwenground/discussions) 中提问
- 加入我们的社区（如果有）
- 查看现有的 Issues 和 PRs

## 📜 行为准则

参与项目时，请：

- 尊重他人
- 保持专业
- 接受建设性批评
- 关注对社区最有利的事情

感谢您的贡献！🎉

