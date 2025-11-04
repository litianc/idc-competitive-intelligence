/**
 * RSSHub自定义路由示例
 *
 * 目标：为中国IDC圈创建RSS订阅
 * 文件位置：RSSHub项目的 lib/routes/idcquan/news.js
 */

const got = require('@/utils/got');
const cheerio = require('cheerio');

module.exports = async (ctx) => {
    // 第1步：定义要抓取的网站
    const baseUrl = 'https://www.idcquan.com';
    const listUrl = `${baseUrl}/news/`;

    // 第2步：访问网站并获取HTML
    const response = await got(listUrl);
    const $ = cheerio.load(response.data);

    // 第3步：解析HTML，提取文章信息
    // （这里的选择器需要根据实际网站调整）
    const items = $('.article-item')  // 假设文章在这个class里
        .toArray()
        .slice(0, 20)  // 只取前20篇
        .map((item) => {
            item = $(item);

            // 提取标题
            const title = item.find('.title').text().trim();

            // 提取链接
            const link = item.find('a').attr('href');
            const fullLink = link.startsWith('http')
                ? link
                : baseUrl + link;

            // 提取日期
            const dateText = item.find('.date').text().trim();
            const pubDate = new Date(dateText);

            // 提取摘要（如果有）
            const description = item.find('.summary').text().trim();

            // 第4步：返回标准RSS格式
            return {
                title: title,
                link: fullLink,
                pubDate: pubDate,
                description: description || title,
            };
        })
        .filter(item => item.title);  // 过滤掉空标题

    // 第5步：设置RSS feed的元信息
    ctx.state.data = {
        title: '中国IDC圈 - 最新新闻',
        link: listUrl,
        description: 'IDC行业权威资讯',
        item: items,
    };
};

/**
 * 使用方法：
 *
 * 1. 启动RSSHub后，访问：
 *    http://localhost:1200/idcquan/news
 *
 * 2. 得到标准RSS输出：
 *    <?xml version="1.0"?>
 *    <rss version="2.0">
 *      <channel>
 *        <title>中国IDC圈 - 最新新闻</title>
 *        <item>
 *          <title>某公司完成15亿融资</title>
 *          <link>https://www.idcquan.com/news/123.html</link>
 *          <pubDate>2025-11-03T10:00:00Z</pubDate>
 *        </item>
 *        ...
 *      </channel>
 *    </rss>
 *
 * 3. 在任何RSS阅读器中订阅这个地址
 */
