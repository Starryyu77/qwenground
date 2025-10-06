# 更新日志

本文档记录 QwenGround 项目的所有重要变更。

## [未发布]

### 新增
- 完整的项目文档结构
- MIT 许可证
- 贡献指南（CONTRIBUTING.md）

### 改进
- 重组文档到 `docs/` 目录
- 优化主 README.md，添加徽章和更好的结构
- 改进 .gitignore 配置

## [0.1.0] - 2025-10-06

### 新增
- 初始项目发布
- 核心功能实现：
  - Perspective Adaptation Module（视角适应模块）
  - 3D Reconstruction（3D重建模块）
  - Object Lookup Table（物体查找表）
  - Fusion Alignment Module（融合对齐模块）
  - Visualization（可视化模块）
- ARKitScenes 数据集支持
- 基础文档和示例代码
- 数据准备脚本
- 依赖检查和安装测试脚本

### 核心模块
- `qwenground_main.py` - 主程序入口
- `qwenground_system.py` - 系统核心实现
- `modules/` - 五个核心功能模块
- `utils/` - 工具类（VLM客户端、物体检测、辅助函数）
- `scripts/` - 实用脚本集合

### 文档
- 项目架构文档
- 安装指南
- 快速开始指南
- ARKitScenes 集成文档
- 中文交付和测试报告

---

## 版本说明

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

### 变更类型
- **新增** - 新功能
- **改进** - 对现有功能的改进
- **修复** - Bug 修复
- **废弃** - 即将移除的功能
- **移除** - 已移除的功能
- **安全** - 安全性相关的修复

