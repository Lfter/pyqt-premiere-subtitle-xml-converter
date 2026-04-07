# srt_to_xml

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

- macOS 13 或更高版本
- Apple Silicon Mac
- Homebrew `python@3.12`
- Adobe Premiere Pro 可导入的 `xmeml` 样式模板文件

## 本地开发安装

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-build.txt
```

如果系统里还没有 `python3.12`，先执行：

```bash
brew install python@3.12
```

构建脚本也支持一个仓库内的备用运行时路径：`.tools/python312/Python.framework`。这主要用于系统级安装受限的情况。

## 源码运行

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
.venv/bin/pytest
```

## 构建 macOS App

项目内置了完整的图标生成和 PyInstaller 打包脚本。执行下面的命令会自动完成：

- 检查 `python3.12`
- 创建或复用 `.venv`
- 安装运行依赖和打包依赖
- 运行测试
- 生成 `assets/macos/srt_to_xml.png`
- 生成 `assets/macos/srt_to_xml.icns`
- 输出 `dist/srt_to_xml.app`

```bash
./scripts/build_macos_app.sh
```

如果你希望显式分步执行，也可以使用：

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-build.txt
.venv/bin/pytest
.venv/bin/python scripts/generate_icon.py
.venv/bin/pyinstaller srt_to_xml.spec --noconfirm --clean
```

## 产物说明

- 交付物是 `dist/srt_to_xml.app`
- 这是一个自包含的 macOS 应用包，目标 Mac 不需要额外安装 Python、PyQt5、lxml 或 srt
- 当前构建目标仅覆盖 Apple Silicon 机器，不兼容 Intel Mac

## 复制到另一台 Mac 的注意事项

- 请复制整个 `srt_to_xml.app`，不要只复制包内的单个可执行文件
- 目标机器建议不低于当前构建机的 macOS 版本
- 如果目标机器从网络、聊天工具或浏览器下载了应用，macOS 可能会附加 quarantine 标记

首次打开未签名应用时，可按下面的方式处理：

1. 在 Finder 中右键 `srt_to_xml.app`
2. 选择“打开”
3. 在系统弹窗中再次确认打开

在受信任的内部环境中，也可以移除 quarantine：

```bash
xattr -dr com.apple.quarantine dist/srt_to_xml.app
```

## 签名与公证

当前仓库已经预留好应用图标、Bundle Identifier 和 PyInstaller app bundle 结构，但默认不执行签名、公证和 stapling。

后续如果要面向外部分发，需要补齐：

- Apple Developer 账号
- `Developer ID Application` 证书
- `xcrun notarytool` 凭据

完成这些前置条件后，再为 `dist/srt_to_xml.app` 增加签名、公证和分发容器即可。

## 发布说明

当前版本号沿用 `0.1.0`。历史变更记录见 [CHANGELOG.md](./CHANGELOG.md)。
