# PyQt Premiere Subtitle XML Converter

将 SRT 字幕批量转换为套用 Premiere 样式模板的 `xmeml` XML。

这个项目提供一个基于 `PyQt5` 的桌面工具，适合把已有的 `.srt` 字幕文件快速转换成可导入 Adobe Premiere Pro 的图形字幕 XML，并继承模板里的位置、字体、颜色和动画样式。

## 功能概览

- 支持拖拽或点击选择 XML 样式模板和 SRT 字幕文件
- 自动识别 Premiere `xmeml` 模板中的 `GraphicAndType` 字幕原型
- 按 SRT 时间批量复制字幕片段并更新 `start`、`end`、`pproTicks` 等字段
- 保留模板中的轨道、分辨率、序列设置和图形样式
- 记住最近一次使用的输入文件和输出目录
- 提供界面内日志与前三条字幕预览

## 环境要求

- Python 3.12 或兼容版本
- Linux、macOS 或 Windows
- Adobe Premiere Pro 可导入的 `xmeml` 样式模板文件

## 安装

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 运行

```bash
.venv/bin/python main.py
```

## 使用流程

1. 准备一个 Premiere 导出的 `xmeml` 样式模板 XML，其中需要保留一个参考字幕片段。
2. 启动程序后，把模板 XML 拖入左侧框，把 `.srt` 文件拖入右侧框。
3. 点击“开始转换”，选择输出 XML 的保存位置。
4. 导出完成后，将生成的 XML 导入 Premiere Pro。

## 模板兼容范围

当前版本优先支持下面这类模板：

- 根节点为 `xmeml`
- 包含 `sequence`
- 在视频轨的某个 `clipitem` 中存在 `effectid=GraphicAndType`
- 该字幕原型含有 `源文本` 或 `Source Text` 参数

如果模板里存在多个可疑字幕原型，程序会直接报错，避免错误覆盖样式。

## 测试

```bash
.venv/bin/python -m pytest
```

## 发布说明

首个公开版本的变更记录见 [CHANGELOG.md](./CHANGELOG.md)。
