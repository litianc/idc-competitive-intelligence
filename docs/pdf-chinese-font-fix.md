# PDF 中文字体问题解决方案

## 问题描述

生成的 PDF 文件中中文显示为乱码或方块。

## 原因分析

Playwright 生成 PDF 时，需要系统安装中文字体才能正确渲染中文字符。默认的 Docker/Linux 环境可能没有安装中文字体。

## 解决方案

### 方案一：安装系统中文字体（推荐）

在服务器上安装中文字体：

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei

# CentOS/RHEL
sudo yum install -y wqy-zenhei-fonts wqy-microhei-fonts

# 验证字体安装
fc-list :lang=zh
```

安装后的字体：
- **Noto Sans CJK SC** - Google 开源中文字体（推荐）
- **WenQuanYi Zen Hei** - 文泉驿正黑
- **WenQuanYi Micro Hei** - 文泉驿微米黑

### 方案二：在 HTML 中指定字体

代码已自动处理，在生成 PDF 时会添加字体声明：

```python
# src/reporting/pdf_generator.py 中的处理
font_style = """
<style>
    body, * {
        font-family: 'Noto Sans CJK SC', 'Source Han Sans CN', 'PingFang SC',
                     'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Hiragino Sans GB',
                     'SimHei', 'STHeiti', sans-serif !important;
    }
</style>
"""
```

这个字体列表的优先级顺序：
1. Noto Sans CJK SC（Linux推荐）
2. Source Han Sans CN（思源黑体）
3. PingFang SC（macOS系统字体）
4. Microsoft YaHei（Windows系统字体）
5. WenQuanYi Micro Hei（文泉驿）
6. 其他中文字体
7. sans-serif（后备字体）

### 方案三：Docker 环境配置

如果在 Docker 容器中运行，需要在 Dockerfile 中添加字体安装：

```dockerfile
# Dockerfile
FROM python:3.9

# 安装中文字体
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 安装 Playwright 浏览器
RUN playwright install chromium
RUN playwright install-deps chromium

# ... 其他配置
```

## 验证方法

### 1. 检查系统字体

```bash
# 列出所有中文字体
fc-list :lang=zh

# 查找特定字体
fc-list | grep -i "noto\|wenquanyi\|hei"
```

### 2. 测试 PDF 生成

```bash
# 运行测试脚本
python3 test_pdf_generation.py

# 检查生成的 PDF
ls -lh reports/*.pdf

# 打开 PDF 文件查看
# 如果中文正常显示，说明问题已解决
```

### 3. 简单测试代码

```python
from src.reporting.pdf_generator import PDFGenerator

test_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
    <h1>中文测试</h1>
    <p>数据中心、云计算、AI算力</p>
    <p>Emoji: 📌 💡 🔥</p>
</body>
</html>
'''

generator = PDFGenerator.from_env()
generator.html_to_pdf(test_html, 'test_chinese.pdf')
print("生成完成，请检查 test_chinese.pdf")
```

## 常见问题

### Q: PDF 中部分字符是方块？

A: 某些特殊字符可能不在字体支持范围内。解决方法：
- 安装更全面的字体（如 Noto Sans CJK 完整版）
- 检查字符是否为特殊符号或生僻字

### Q: PDF 文件很大（>2MB）？

A: 可能是因为嵌入了完整字体。解决方法：
- 使用系统字体而不是在线字体
- 代码已优化为使用系统字体，重新生成即可

### Q: macOS/Windows 上正常，Linux 上乱码？

A: 因为 macOS/Windows 默认有中文字体，Linux 需要手动安装。按照上述步骤安装字体即可。

### Q: Docker 容器中字体安装失败？

A: 检查以下几点：
- 确保 Dockerfile 中有 `apt-get update`
- 确认网络连接正常
- 使用正确的包管理器（apt/yum）

## 字体选择建议

| 环境 | 推荐字体 | 安装命令 |
|------|---------|---------|
| Ubuntu/Debian | Noto Sans CJK SC | `apt-get install fonts-noto-cjk` |
| CentOS/RHEL | WenQuanYi Zen Hei | `yum install wqy-zenhei-fonts` |
| macOS | 系统自带 PingFang SC | 无需安装 |
| Windows | 系统自带 Microsoft YaHei | 无需安装 |
| Docker | Noto Sans CJK SC | 见上方 Dockerfile |

## 性能影响

安装中文字体后：
- **PDF 生成时间**: 无明显影响（3-5秒）
- **PDF 文件大小**: 700-800KB（使用系统字体，不嵌入字体数据）
- **内存占用**: 增加约 50-100MB（字体文件加载）

## 更新日志

- **2025-11-08**:
  - 修复 PDF 中文乱码问题
  - 添加系统字体回退列表
  - 优化字体加载逻辑
  - 添加字体安装文档

---

最后更新：2025-11-08
