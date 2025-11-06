"""
内容分类系统

支持4类内容分类：
1. 投资动态
2. 技术进展
3. 政策法规  
4. 市场动态

每篇文章可属于多个类别，按优先级排序：投资 > 技术 > 政策 > 市场
"""

from typing import List, Optional


class CategoryClassifier:
    """内容分类器"""

    # 分类1：投资动态
    INVESTMENT_KEYWORDS = [
        '融资', '投资', '并购', '收购', 'IPO', '估值', '轮次',
        '风投', 'PE', 'VC', '募资', '资本', '股权', '上市', '挂牌'
    ]

    # 分类2：技术进展  
    TECHNOLOGY_KEYWORDS = [
        'GPU', '芯片', '处理器', '算力', '液冷', '风冷', '散热',
        '制冷', '新品', '发布', '推出', '上线', '技术', '突破',
        '创新', '研发', 'AI模型', '训练', '推理', '性能', '效率', '优化'
    ]

    # 分类3：政策法规
    POLICY_KEYWORDS = [
        # 通用政策词汇
        '政策', '法规', '标准', '规范', '监管', '审批', '许可',
        '备案', '规划', '指导', '意见', '通知', '国家', '政府',
        '工信部', '发改委', '条例', '办法', '细则',
        # 政府部门和机构
        '国家数据局', '网信办', '能源局', '部门', '五部门', '三部门', '六部门',
        # IDC专项政策
        '东数西算', '数据基础设施', '算力网', '新基建', '数据要素',
        'PUE', '能耗双控', '绿色数据中心', '数据安全', '数据中心规划',
        # 政策行动
        '优化改造', '试点', '示范', '合规', '要求', '指南',
        '行动计划', '实施方案', '管理条例', '管理办法',
        # 政策文件和报告
        '白皮书', '蓝皮书', '政策解读', '政府文件', '发文', '印发'
    ]

    # 分类4：市场动态
    MARKET_KEYWORDS = [
        '市场', '份额', '排名', '占比', '增长', '下滑', '趋势',
        '预测', '报告', '分析', '研究', '调研', '需求', '供给',
        '竞争', '格局', '价格', '成本', '利润'
    ]

    # 分类优先级
    CATEGORY_PRIORITY = ['投资', '技术', '政策', '市场']

    def classify(self, title: Optional[str], content: Optional[str]) -> List[str]:
        """
        分类文章内容

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            分类列表，按优先级排序
        """
        if not title:
            title = ""
        if not content:
            content = ""

        text = title + " " + content
        categories = []

        # 检查投资类
        if self._has_keywords(text, self.INVESTMENT_KEYWORDS):
            categories.append('投资')

        # 检查技术类
        if self._has_keywords(text, self.TECHNOLOGY_KEYWORDS):
            categories.append('技术')

        # 检查政策类
        if self._has_keywords(text, self.POLICY_KEYWORDS):
            categories.append('政策')

        # 检查市场类
        if self._has_keywords(text, self.MARKET_KEYWORDS):
            categories.append('市场')

        # 如果没有匹配任何类别，归为"其他"
        if not categories:
            categories.append('其他')

        return categories

    def _has_keywords(self, text: str, keywords: List[str]) -> bool:
        """检查文本中是否包含任意关键词"""
        for keyword in keywords:
            if keyword in text:
                return True
        return False
