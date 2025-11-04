# RSSHub自定义路由详解

## 🤔 RSSHub到底在做什么？

**简单说：RSSHub = RSS订阅生成器**

它的作用是：**把没有RSS的网站，变成有RSS**

---

## 📊 对比图

### 场景A：网站有原生RSS（理想情况）

```
┌─────────────┐
│  新闻网站    │
│             │  提供RSS
│  www.xxx.cn │ ─────────► RSS阅读器可以直接订阅
│             │            http://www.xxx.cn/rss.xml
└─────────────┘
```

**例子：**
- 微信公众号 ✅ 有RSS（通过第三方）
- B站UP主 ✅ 有RSS（通过RSSHub官方）
- 知乎专栏 ✅ 有RSS（通过RSSHub官方）

---

### 场景B：网站无RSS（我们的情况）

```
┌─────────────┐
│  IDC网站    │
│             │  ❌ 没有RSS
│  idcquan.cn │
│             │  只有普通网页
└─────────────┘
       │
       │ 你需要手动访问
       ↓
   每天检查新闻
```

---

### 场景C：使用RSSHub自定义路由（解决方案）

```
┌─────────────┐
│  IDC网站    │
│             │
│  idcquan.cn │
└─────────────┘
       │
       │ RSSHub路由脚本自动抓取
       ↓
┌─────────────┐
│   RSSHub    │  转换成RSS格式
│  (你部署)   │ ──────────► RSS阅读器订阅
│             │              http://localhost:1200/idcquan/news
└─────────────┘
```

---

## 🔧 创建路由 = 写一个转换器

### 步骤拆解

**输入：** 网页HTML

```html
<!-- idcquan.com的HTML片段 -->
<div class="news-item">
  <h3 class="title">
    <a href="/news/123.html">某公司完成15亿融资</a>
  </h3>
  <span class="date">2025-11-03</span>
</div>
```

**处理：** RSSHub路由脚本

```javascript
// 你写的代码：解析HTML
const title = $('.title a').text();        // "某公司完成15亿融资"
const link = $('.title a').attr('href');   // "/news/123.html"
const date = $('.date').text();            // "2025-11-03"
```

**输出：** 标准RSS XML

```xml
<item>
  <title>某公司完成15亿融资</title>
  <link>https://www.idcquan.com/news/123.html</link>
  <pubDate>Mon, 03 Nov 2025 00:00:00 GMT</pubDate>
</item>
```

---

## 💡 核心工作

创建RSSHub路由要做3件事：

### 1. 分析网站结构（最重要）

```bash
# 使用我写的工具
python tmp/analyze_website.py https://www.idcquan.com
```

找到：
- ✅ 文章列表在哪个元素里
- ✅ 标题的CSS选择器
- ✅ 链接的CSS选择器
- ✅ 日期的CSS选择器

### 2. 编写路由脚本

```javascript
// 告诉RSSHub如何从HTML提取信息
module.exports = async (ctx) => {
    // 访问网站
    const response = await got('https://www.idcquan.com/news/');

    // 解析HTML
    const $ = cheerio.load(response.data);

    // 提取文章
    const items = $('.article-item').map((item) => {
        return {
            title: $(item).find('.title').text(),
            link: $(item).find('a').attr('href'),
            pubDate: $(item).find('.date').text()
        };
    });

    // 返回RSS格式
    ctx.state.data = { title: 'IDC圈新闻', item: items };
};
```

### 3. 配置路由规则

```javascript
// 告诉RSSHub这个路由的访问路径
module.exports = function (router) {
    router.get('/news', require('./news'));  // 访问: /idcquan/news
    router.get('/tech', require('./tech'));  // 访问: /idcquan/tech
};
```

---

## 🎯 实际效果

### 部署后的使用

```bash
# 1. 启动RSSHub
docker run -d -p 1200:1200 diygod/rsshub

# 2. 访问自定义路由
http://localhost:1200/idcquan/news

# 3. 得到RSS订阅地址
# 在任何RSS阅读器中添加这个地址即可
```

### 在RSS阅读器中

```
📰 中国IDC圈 - 最新新闻 (20)

├── [今天] 某公司完成15亿融资建设AI算力中心
├── [今天] 新型液冷技术突破PUE 1.1极限
├── [昨天] 工信部发布数据中心能效新标准
└── [2天前] 2024年IDC市场规模突破3000亿
```

你只需要在阅读器里查看，不用每天访问网站！

---

## 🆚 对比：自定义路由 vs 直接爬虫

### 方案A：RSSHub自定义路由

**你需要做：**
```javascript
// 1. 写一个50行的JS文件（路由脚本）
// 2. 放到RSSHub的routes目录
// 3. 重启RSSHub
```

**优势：**
- ✅ 标准RSS输出（任何阅读器都能用）
- ✅ RSSHub自动处理缓存、定时抓取
- ✅ 可以给其他人用
- ✅ 维护简单（只需更新一个文件）

**劣势：**
- ⚠️ 需要部署RSSHub服务
- ⚠️ 需要学习RSSHub的API

---

### 方案B：直接写Python爬虫

**你需要做：**
```python
# 1. 写爬虫脚本
# 2. 写定时任务
# 3. 写数据存储
# 4. 写去重逻辑
# 5. 写错误处理
```

**优势：**
- ✅ 完全掌控，想怎么改就怎么改
- ✅ 可以抓取更多信息（如全文）
- ✅ 直接存入你的数据库

**劣势：**
- ⚠️ 代码量更大
- ⚠️ 需要自己维护所有逻辑
- ⚠️ 不是标准RSS格式

---

## 🎯 我的推荐

### 对于你的情况（IDC情报系统）

**推荐：直接写Python爬虫**（方案B）

**原因：**
1. ✅ 你已经有数据库和处理流程
2. ✅ 需要评分、分类等自定义逻辑
3. ✅ 需要集成LLM摘要生成
4. ✅ 不需要给其他人提供RSS订阅

**RSSHub更适合：**
- 想订阅各种网站到RSS阅读器
- 需要分享RSS给团队
- 想要标准化的RSS输出

---

## 📂 工作量对比

### RSSHub自定义路由

```
准备工作：
- 安装Docker ........................ 10分钟
- 部署RSSHub ........................ 5分钟
- 克隆RSSHub代码 .................... 5分钟

开发工作：
- 分析网站结构 ...................... 30分钟
- 编写路由脚本（1个网站） ........... 30分钟
- 测试调试 .......................... 20分钟
- 重复2个网站 ....................... 1小时

总计：约2.5-3小时
```

### Python爬虫（你已经有大部分代码）

```
已完成：
✅ 数据库层
✅ 评分系统
✅ 分类系统
✅ 爬虫框架

还需要：
- 分析3个网站结构 ................... 30分钟
- 更新选择器配置 .................... 15分钟
- 测试运行 .......................... 15分钟

总计：约1小时
```

---

## 🚀 建议行动方案

**现在立即做：**
```bash
# 使用你已有的Python爬虫
# 只需要配置选择器就能工作

python tmp/analyze_website.py https://www.idcquan.com
# 告诉我网站的HTML结构
# 我更新选择器
# 15分钟内开始采集真实数据
```

**以后有空做：**
- 学习RSSHub路由开发
- 创建标准RSS输出
- 可以分享给团队订阅

---

## 📖 总结

**RSSHub自定义路由 = 网页转RSS的自动化脚本**

**本质上和你的Python爬虫做的是同一件事，只是：**
- RSSHub输出标准RSS格式（给RSS阅读器用）
- 你的爬虫输出到数据库（给周报系统用）

**你的需求更适合用Python爬虫，因为：**
- ✅ 代码已经写了大半
- ✅ 需要深度集成（评分、分类、LLM）
- ✅ 不需要RSS格式输出

想继续用Python爬虫方案吗？只需要15分钟配置就能开始采集数据了！
