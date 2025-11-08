#!/bin/bash
# 测试定时任务会执行的命令
# 这是定时任务实际运行的命令的模拟

echo "========================================================================"
echo "定时任务命令测试"
echo "========================================================================"
echo ""
echo "模拟定时任务执行的确切命令："
echo "  python3 generate_weekly_report.py --days 7 --send-email"
echo ""
echo "========================================================================"
echo ""

# 询问是否执行
read -p "是否执行此命令？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo ""
    echo "开始执行..."
    echo "========================================================================"
    echo ""

    # 执行命令
    python3 generate_weekly_report.py --days 7 --send-email

    EXIT_CODE=$?

    echo ""
    echo "========================================================================"
    echo "执行完成"
    echo "========================================================================"
    echo ""
    echo "退出代码: $EXIT_CODE"

    if [ $EXIT_CODE -eq 0 ]; then
        echo "状态: ✓ 成功"
        echo ""
        echo "请检查："
        echo "1. 邮箱是否收到邮件"
        echo "2. 邮件正文是否正常显示（包括在苹果邮件中）"
        echo "3. 是否有PDF附件"
        echo "4. PDF中emoji是否正常显示"
        echo "5. 收件人地址是否正常（无@domain.invalid）"
        echo ""
        echo "生成的文件："
        ls -lh reports/ | tail -5
    else
        echo "状态: ✗ 失败"
        echo ""
        echo "请检查错误信息并参考故障排查文档："
        echo "  docs/troubleshooting.md"
    fi
else
    echo ""
    echo "已取消执行"
fi

echo ""
