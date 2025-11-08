# 快速修复参考

## 问题 1: 苹果邮件只显示附件不显示正文

```python
# ❌ 错误写法
message = MIMEMultipart('alternative')

# ✅ 正确写法
message = MIMEMultipart('mixed' if attachments else 'alternative')
```

**文件：** `src/notification/email_sender.py:78`

---

## 问题 2: 邮件收件人显示 @domain.invalid

```python
# ❌ 错误写法
message['To'] = Header(', '.join(recipients), 'utf-8')

# ✅ 正确写法
message['To'] = ', '.join(recipients)
```

**文件：** `src/notification/email_sender.py:79-85`

---

## 问题 3: PDF 中 emoji 不显示

### 步骤 1: 安装字体
```bash
sudo apt-get install -y fonts-noto-color-emoji
```

### 步骤 2: 更新代码
```python
# 在 font-family 末尾添加 emoji 字体
font-family: ..., sans-serif, 'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji' !important;
```

**文件：** `src/reporting/pdf_generator.py:70-73`

---

## 验证测试

```bash
# 综合测试
python3 test_both_fixes.py

# 单独测试
python3 test_email_mime_structure.py  # 苹果邮件显示问题
python3 test_email_recipient_fix.py   # 收件人地址问题
python3 test_pdf_emoji.py             # PDF emoji问题
```

---

## 相关文档

- 详细修复说明：`docs/fixes-2025-11-08.md`
- 故障排查指南：`docs/troubleshooting.md`
