#!/usr/bin/env python3
"""
全球赢必看的新闻资讯 - 云端版
1. 抓取 RSS 源获取最新资讯
2. 生成静态 HTML 页面（GitHub Pages 托管）
3. 可选：推送摘要到微信（Server酱）
"""

import feedparser
import requests
import os
import re
import html
from datetime import datetime, timezone, timedelta

# ============================================================
# RSS 源配置
# ============================================================
RSS_FEEDS = {
    'trade': [
        'http://www.people.com.cn/rss/finance.xml',
        'https://www.chinanews.com.cn/rss/cj.xml',
    ],
    'cross': [
        'http://www.people.com.cn/rss/finance.xml',
        'https://www.chinanews.com.cn/rss/cj.xml',
    ],
    'intl': [
        'http://www.people.com.cn/rss/world.xml',
        'https://www.chinanews.com.cn/rss/gj.xml',
    ],
    'domestic': [
        'http://www.people.com.cn/rss/politics.xml',
        'https://www.chinanews.com.cn/rss/gn.xml',
    ],
}

# 外贸关键词筛选
TRADE_KEYWORDS = [
    '关税', '出口', '进口', '贸易', '海关', '外贸', 'WTO', '反倾销',
    '出口管制', '制裁', '关税法', '进出口', '自贸', '壁垒', '协定',
    '关税壁垒', 'shipping', 'freight', '集装箱', '港口',
]
CROSS_KEYWORDS = [
    '跨境', '电商', 'TikTok', 'Temu', 'SHEIN', '亚马逊', 'AliExpress',
    '速卖通', 'eBay', '海外仓', '直邮', 'B2B', '出海', '平台',
    '小程序', '直播带货', '独立站', 'Shopee', 'Lazada',
]

# ============================================================
# 板块配置
# ============================================================
SECTIONS = {
    'trade': {
        'title': '外贸重点资讯',
        'sub': '关税政策 · 出口管制 · 贸易摩擦 · 行业出海',
        'emoji': '📈',
        'badge': 'trade',
        'thumb': 'thumb-trade',
        'tag': 'tag-trade',
        'ranked': False,
        'max': 8,
    },
    'cross': {
        'title': '跨境热点信息',
        'sub': '平台动态 · 合规监管 · 出海趋势',
        'emoji': '🛒',
        'badge': 'cross',
        'thumb': 'thumb-cross',
        'tag': 'tag-cross',
        'ranked': False,
        'max': 6,
    },
    'intl': {
        'title': '十大国际新闻',
        'sub': '全球重大事件 · 地缘政治 · 财经',
        'emoji': '🌍',
        'badge': 'intl',
        'thumb': 'thumb-intl',
        'tag': 'tag-intl',
        'ranked': True,
        'max': 10,
    },
    'domestic': {
        'title': '国内十大新闻',
        'sub': '经济政策 · 产业数据 · 社会热点',
        'emoji': '🇨🇳',
        'badge': 'domestic',
        'thumb': 'thumb-domestic',
        'tag': 'tag-domestic',
        'ranked': True,
        'max': 10,
    },
}


# ============================================================
# 工具函数
# ============================================================
def get_emoji(title, summary=''):
    text = title + summary
    emoji_map = [
        (['关税', '税率', '加征'], '🏛️'),
        (['出口管制', '制裁', '禁令', '管制'], '🛡️'),
        (['冲突', '战争', '空袭', '导弹', '袭击', '轰炸'], '💥'),
        (['油价', '原油', '石油'], '🛢️'),
        (['黄金', '避险', '金价'], '🥇'),
        (['汇率', '美元', '欧元', '人民币', '外汇'], '💱'),
        (['数据', '增长', '进出口', '统计'], '📊'),
        (['电商', '跨境', '平台', '网购'], '🛒'),
        (['AI', '人工智能', '科技', '芯片', 'OpenAI', '模型'], '🤖'),
        (['航天', '火箭', '发射', '卫星'], '🚀'),
        (['会议', '会见', '会谈', '外交', '峰会'], '🤝'),
        (['政策', '规划', '改革', '方案', '意见'], '📋'),
        (['就业', '民生', '收入', '工资'], '👷'),
        (['消费', '零售', '市场', '以旧换新'], '🛍️'),
        (['能源', '电力', '太阳能', '风电', '新能源'], '⚡'),
        (['气象', '高温', '台风', '暴雨', '天气'], '🌡️'),
        (['体育', '足球', '奥运', '世界杯'], '⚽'),
        (['教育', '学校', '学生', '基础教育'], '📚'),
        (['造船', '航运', '港口', '船舶'], '🚢'),
        (['医疗', '健康', '卫生', '药'], '🏥'),
        (['房地产', '楼市', '住房'], '🏠'),
        (['汽车', '新能源车', '电动车', '比亚迪', '特斯拉'], '🚗'),
        (['美国', '美方', '特朗普', '拜登'], '🇺🇸'),
        (['欧盟', '欧洲', '欧委会'], '🇪🇺'),
        (['日本', '日方'], '🇯🇵'),
        (['韩国', '韩方'], '🇰🇷'),
        (['俄罗斯', '俄方', '普京'], '🇷🇺'),
        (['乌克兰', '泽连斯基'], '🇺🇦'),
        (['伊朗', '中东', '以色列'], '💣'),
        (['印度', '印方'], '🇮🇳'),
        (['巴西', '拉美'], '🇧🇷'),
        (['东南亚', '东盟', '越南', '泰国'], '🌏'),
        (['非洲'], '🌍'),
    ]
    for keywords, emoji in emoji_map:
        for kw in keywords:
            if kw in text:
                return emoji
    return '📰'


def extract_tags(title, summary=''):
    text = title + summary
    tag_map = {
        '关税': ['关税', '税率', '加征', '附加税', '豁免'],
        '出口管制': ['出口管制', '禁令', '制裁', '管制清单'],
        '贸易摩擦': ['反倾销', '壁垒', '摩擦', '争端', '报复'],
        '进出口': ['进出口', '出口额', '进口额', '海关', '贸易额'],
        '跨境电商': ['跨境', '电商', 'TikTok', 'Temu', 'SHEIN', 'Shopee'],
        '平台': ['亚马逊', 'eBay', '速卖通', 'AliExpress', '阿里'],
        '美国': ['美国', '美方', '特朗普', '拜登', '白宫'],
        '欧盟': ['欧盟', '欧洲', '欧委会', '法国', '德国'],
        '冲突': ['冲突', '战争', '空袭', '导弹', '袭击', '停火'],
        '油价': ['油价', '原油', '石油', 'OPEC'],
        '黄金': ['黄金', '金价', '避险'],
        'AI': ['AI', '人工智能', 'OpenAI', '大模型', 'GPT'],
        '政策': ['政策', '规划', '改革', '方案', '意见', '措施'],
        '数据': ['数据', '增长', '统计', '指标'],
        '外交': ['会见', '会谈', '外交', '外长', '访问'],
        '就业': ['就业', '失业', '民生', '工资'],
        '消费': ['消费', '零售', '以旧换新', '内需'],
        '能源': ['能源', '电力', '太阳能', '风电', '新能源'],
        '科技': ['科技', '芯片', '半导体', '量子'],
        '航天': ['航天', '火箭', '发射', '卫星', '空间站'],
    }
    tags = []
    for tag, keywords in tag_map.items():
        for kw in keywords:
            if kw in text:
                tags.append(tag)
                break
        if len(tags) >= 2:
            break
    if len(tags) < 1:
        tags.append('资讯')
    if len(tags) < 2:
        tags.append('热点')
    return tags[:2]


def parse_date(entry):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
            return dt.strftime('%m-%d')
    except:
        pass
    return datetime.now(timezone(timedelta(hours=8))).strftime('%m-%d')


def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def truncate_summary(text, max_len=60):
    text = clean_text(text)
    if len(text) > max_len:
        text = text[:max_len] + '…'
    return text


def get_source(link, feed_url):
    if 'people.com.cn' in link or 'people.com.cn' in feed_url:
        return '人民日报'
    if 'chinanews.com' in link or 'chinanews.com' in feed_url:
        return '中国新闻网'
    if 'customs.gov.cn' in link:
        return '海关总署'
    if 'xinhua' in link or 'news.cn' in link:
        return '新华社'
    if 'cctv.com' in link or 'cctv.cn' in link:
        return '央视新闻'
    if 'caixin' in link:
        return '财新'
    if 'nbd.com' in link:
        return '每日经济新闻'
    if 'cls.cn' in link or 'caixin' in link:
        return '财联社'
    return '综合报道'


# ============================================================
# RSS 抓取与分类
# ============================================================
def fetch_rss(url):
    try:
        resp = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
        })
        feed = feedparser.parse(resp.content)
        print(f"  [{feed_url_short(url)}] fetched {len(feed.entries)} entries")
        return feed.entries
    except Exception as e:
        print(f"  [{feed_url_short(url)}] ERROR: {e}")
        return []


def feed_url_short(url):
    if 'people.com.cn' in url:
        if 'finance' in url:
            return '人民日报·财经'
        if 'world' in url:
            return '人民日报·国际'
        if 'politics' in url:
            return '人民日报·时政'
    if 'chinanews.com' in url:
        if 'cj' in url:
            return '中新网·财经'
        if 'gj' in url:
            return '中新网·国际'
        if 'gn' in url:
            return '中新网·国内'
    return url[:30]


def collect_news():
    print("=== 开始抓取 RSS 源 ===")
    result = {}

    for section_key, section_config in SECTIONS.items():
        print(f"\n--- 板块: {section_config['title']} ---")
        all_entries = []
        for url in RSS_FEEDS[section_key]:
            entries = fetch_rss(url)
            for entry in entries:
                entry._feed_url = url
            all_entries.extend(entries)

        # 外贸/跨境板块需要按关键词筛选
        if section_key == 'trade':
            filtered = []
            for entry in all_entries:
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                if any(kw in title + summary for kw in TRADE_KEYWORDS):
                    filtered.append(entry)
            all_entries = filtered if len(filtered) >= 3 else all_entries
            print(f"  关键词筛选后: {len(all_entries)} 条")
        elif section_key == 'cross':
            filtered = []
            for entry in all_entries:
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                if any(kw in title + summary for kw in CROSS_KEYWORDS):
                    filtered.append(entry)
            all_entries = filtered if len(filtered) >= 2 else all_entries
            print(f"  关键词筛选后: {len(all_entries)} 条")

        # 去重并整理
        seen_titles = set()
        items = []
        for entry in all_entries:
            title = clean_text(entry.get('title', '')).strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            summary = truncate_summary(entry.get('summary', entry.get('description', '')))
            link = entry.get('link', '')
            feed_url = getattr(entry, '_feed_url', '')
            source = get_source(link, feed_url)

            items.append({
                'tags': extract_tags(title, summary),
                'date': parse_date(entry),
                'emoji': get_emoji(title, summary),
                'title': title,
                'summary': summary,
                'source': source,
                'url': link,
            })
            if len(items) >= section_config['max']:
                break

        # 如果不够，补充未筛选的条目
        if len(items) < section_config['max']:
            for entry in all_entries:
                title = clean_text(entry.get('title', '')).strip()
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                summary = truncate_summary(entry.get('summary', entry.get('description', '')))
                link = entry.get('link', '')
                feed_url = getattr(entry, '_feed_url', '')
                source = get_source(link, feed_url)
                items.append({
                    'tags': extract_tags(title, summary),
                    'date': parse_date(entry),
                    'emoji': get_emoji(title, summary),
                    'title': title,
                    'summary': summary,
                    'source': source,
                    'url': link,
                })
                if len(items) >= section_config['max']:
                    break

        result[section_key] = items
        print(f"  最终: {len(items)} 条")

    return result


# ============================================================
# HTML 生成
# ============================================================
def generate_html(news_data, output_path='index.html'):
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    updated = now.strftime('%Y-%m-%d %H:%M')

    def card_html(item, section, thumb_class, tag_class, rank):
        tags = ''.join(f'<span class="tag {tag_class}">{t}</span>' for t in item['tags'])
        rank_html = f'<span class="rank">{str(rank).zfill(2)}</span>' if rank else ''
        return f"""
    <article class="card {section}">
      {rank_html}
      <div class="card-thumb {thumb_class}">
        <span class="emoji">{item['emoji']}</span>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-tags">{tags}</div>
          <span class="card-date">{item['date']}</span>
        </div>
        <a class="card-title-link" href="{item['url']}" target="_blank" rel="noopener noreferrer">
          <h3>{item['title']} <span class="ext-icon">↗</span></h3>
        </a>
        <p>{item['summary']}</p>
        <div class="card-source">📎 {item['source']}</div>
      </div>
    </article>"""

    def section_html(section_key):
        config = SECTIONS[section_key]
        items = news_data[section_key]
        if not items:
            return f"""
    <section class="section">
      <div class="section-header">
        <div class="section-title">
          <div class="badge {config['badge']}">{config['emoji']}</div>
          <div>
            <h2>{config['title']} <span class="live-tag">每日更新</span></h2>
            <div class="sub">{config['sub']}</div>
          </div>
        </div>
        <span class="count-pill">0 条</span>
      </div>
      <div class="grid {config['ranked'] and 'rank-grid' or 'two-col'}">
        <p style="color:#9aa7b8;padding:20px;">暂无数据</p>
      </div>
    </section>"""

        cards = []
        for i, item in enumerate(items):
            rank = i + 1 if config['ranked'] else None
            cards.append(card_html(item, config['badge'], config['thumb'], config['tag'], rank))
        cards_html = ''.join(cards)

        grid_class = 'rank-grid' if config['ranked'] else 'two-col'
        return f"""
    <section class="section">
      <div class="section-header">
        <div class="section-title">
          <div class="badge {config['badge']}">{config['emoji']}</div>
          <div>
            <h2>{config['title']} <span class="live-tag">每日更新</span></h2>
            <div class="sub">{config['sub']}</div>
          </div>
        </div>
        <span class="count-pill">{len(items)} 条</span>
      </div>
      <div class="grid {grid_class}">{cards_html}</div>
    </section>"""

    sections_html = ''.join(section_html(key) for key in ['trade', 'cross', 'intl', 'domestic'])

    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全球赢必看的新闻资讯</title>
<style>
  :root {{
    --bg: #f6f8fb;
    --bg-card: #ffffff;
    --border: #e8edf3;
    --border-strong: #d4dce6;
    --text: #1a2332;
    --text-dim: #5a6a7e;
    --text-faint: #9aa7b8;
    --c-trade: #0891b2;
    --c-cross: #d97706;
    --c-intl: #dc2626;
    --c-domestic: #7c3aed;
    --c-green: #16a34a;
    --shadow: 0 1px 3px rgba(15,40,80,0.06), 0 1px 2px rgba(15,40,80,0.04);
    --shadow-hover: 0 8px 24px rgba(15,40,80,0.12);
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh; line-height: 1.65;
  }}
  .topbar {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(255,255,255,0.95); backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px; display: flex; align-items: center; justify-content: space-between;
    gap: 16px; flex-wrap: wrap;
  }}
  .brand {{ display: flex; align-items: center; gap: 12px; }}
  .brand-icon {{
    width: 42px; height: 42px; border-radius: 10px;
    background: linear-gradient(135deg, var(--c-trade), #6366f1);
    display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(8,145,178,0.3);
  }}
  .brand-text h1 {{ font-size: 20px; font-weight: 700; letter-spacing: 0.3px; }}
  .brand-text p {{ font-size: 12.5px; color: var(--text-faint); letter-spacing: 0.6px; }}
  .status-group {{ display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }}
  .status-item {{ display: flex; align-items: center; gap: 7px; font-size: 14px; color: var(--text-dim); }}
  .status-item .dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--c-green); box-shadow: 0 0 6px rgba(22,163,74,0.5); animation: pulse 2s infinite;
  }}
  @keyframes pulse {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.35;}} }}
  .status-item .val {{ color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }}
  main {{ max-width: 1300px; margin: 0 auto; padding: 22px 24px 50px; }}
  .section {{ margin-bottom: 36px; }}
  .section-header {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 16px; gap: 10px; flex-wrap: wrap;
  }}
  .section-title {{ display: flex; align-items: center; gap: 12px; }}
  .section-title .badge {{
    width: 38px; height: 38px; border-radius: 9px;
    display: flex; align-items: center; justify-content: center; font-size: 19px; flex-shrink: 0;
  }}
  .badge.trade {{ background: #ecfeff; border: 1px solid #cffafe; }}
  .badge.cross {{ background: #fffbeb; border: 1px solid #fef3c7; }}
  .badge.intl {{ background: #fef2f2; border: 1px solid #fee2e2; }}
  .badge.domestic {{ background: #f5f3ff; border: 1px solid #ede9fe; }}
  .section-title h2 {{ font-size: 19px; font-weight: 700; }}
  .section-title .sub {{ font-size: 12.5px; color: var(--text-faint); margin-top: 1px; }}
  .count-pill {{
    font-size: 13px; color: var(--text-dim);
    background: #fff; border: 1px solid var(--border);
    padding: 4px 12px; border-radius: 13px; font-variant-numeric: tabular-nums;
  }}
  .live-tag {{
    font-size: 11px; color: var(--c-green); font-weight: 700;
    background: #f0fdf4; border: 1px solid #bbf7d0;
    padding: 2px 8px; border-radius: 10px; letter-spacing: 0.3px;
  }}
  .grid {{ display: grid; gap: 12px; }}
  .grid.two-col {{ grid-template-columns: repeat(auto-fill, minmax(440px, 1fr)); }}
  .grid.rank-grid {{ grid-template-columns: repeat(auto-fill, minmax(440px, 1fr)); }}
  .card {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; transition: all 0.2s ease;
    overflow: hidden; display: flex; flex-direction: row;
    box-shadow: var(--shadow); position: relative;
  }}
  .card:hover {{ border-color: var(--border-strong); transform: translateY(-2px); box-shadow: var(--shadow-hover); }}
  .card-thumb {{
    width: 110px; min-height: 130px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 42px; position: relative; overflow: hidden;
  }}
  .card-thumb::after {{
    content: ""; position: absolute; inset: 0;
    background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.25), transparent 60%);
  }}
  .card-thumb .emoji {{ position: relative; z-index: 1; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15)); }}
  .thumb-trade {{ background: linear-gradient(135deg, #0891b2, #065f66); }}
  .thumb-cross {{ background: linear-gradient(135deg, #d97706, #92560a); }}
  .thumb-intl {{ background: linear-gradient(135deg, #dc2626, #8b1818); }}
  .thumb-domestic {{ background: linear-gradient(135deg, #7c3aed, #4c2a96); }}
  .card-body {{ flex: 1; padding: 13px 16px 12px; display: flex; flex-direction: column; min-width: 0; }}
  .card-top {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; gap: 8px; }}
  .card-tags {{ display: flex; gap: 5px; flex-wrap: wrap; }}
  .tag {{ font-size: 11px; padding: 2px 9px; border-radius: 10px; font-weight: 600; white-space: nowrap; }}
  .tag-trade {{ background: #ecfeff; color: var(--c-trade); border: 1px solid #cffafe; }}
  .tag-cross {{ background: #fffbeb; color: var(--c-cross); border: 1px solid #fef3c7; }}
  .tag-intl {{ background: #fef2f2; color: var(--c-intl); border: 1px solid #fee2e2; }}
  .tag-domestic {{ background: #f5f3ff; color: var(--c-domestic); border: 1px solid #ede9fe; }}
  .card-date {{ font-size: 12.5px; color: var(--text-faint); font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .card-title-link {{ text-decoration: none; color: var(--text); display: block; margin-bottom: 5px; }}
  .card-title-link h3 {{
    font-size: 15.5px; font-weight: 600; line-height: 1.5; color: var(--text);
    transition: color 0.15s; display: flex; align-items: flex-start; gap: 5px;
  }}
  .card-title-link:hover h3 {{ color: var(--c-trade); }}
  .card.cross .card-title-link:hover h3 {{ color: var(--c-cross); }}
  .card.intl .card-title-link:hover h3 {{ color: var(--c-intl); }}
  .card.domestic .card-title-link:hover h3 {{ color: var(--c-domestic); }}
  .card-title-link .ext-icon {{ font-size: 12px; opacity: 0.3; flex-shrink: 0; margin-top: 3px; transition: opacity 0.15s; }}
  .card-title-link:hover .ext-icon {{ opacity: 0.8; }}
  .card p {{ font-size: 13.5px; color: var(--text-dim); line-height: 1.6; }}
  .card-source {{ margin-top: auto; padding-top: 7px; font-size: 12px; color: var(--text-faint); display: flex; align-items: center; gap: 4px; }}
  .card.intl .rank, .card.domestic .rank {{
    position: absolute; top: 8px; right: 12px;
    font-size: 28px; font-weight: 800; font-variant-numeric: tabular-nums; line-height: 1; z-index: 2;
  }}
  .card.intl .rank {{ color: rgba(220,38,38,0.12); }}
  .card.domestic .rank {{ color: rgba(124,58,237,0.12); }}
  footer {{
    text-align: center; padding: 26px; color: var(--text-faint);
    font-size: 12.5px; border-top: 1px solid var(--border);
  }}
  footer p {{ margin-bottom: 4px; }}
  @media (max-width: 640px) {{
    .topbar {{ padding: 11px 14px; }}
    main {{ padding: 18px 14px 40px; }}
    .grid.two-col, .grid.rank-grid {{ grid-template-columns: 1fr; }}
    .brand-text h1 {{ font-size: 16px; }}
    .status-group {{ gap: 12px; }}
    .card-thumb {{ width: 80px; min-height: 110px; font-size: 32px; }}
    .card-body {{ padding: 10px 13px 10px; }}
    .card-title-link h3 {{ font-size: 14.5px; }}
  }}
  ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border-strong); border-radius: 4px; }}
</style>
</head>
<body>

<header class="topbar">
  <div class="brand">
    <div class="brand-icon">🌐</div>
    <div class="brand-text">
      <h1>全球赢必看的新闻资讯</h1>
      <p>Daily Trade Intelligence · 每小时自动更新 · 点击标题查看原文</p>
    </div>
  </div>
  <div class="status-group">
    <div class="status-item">
      <span class="dot"></span>
      <span class="val">更新于 {updated}</span>
    </div>
  </div>
</header>

<main>
{sections_html}
</main>

<footer>
  <p>数据来源：人民日报 · 中国新闻网 等公开 RSS 源</p>
  <p>由 GitHub Actions 每小时自动更新 · 点击卡片标题可跳转原文查看详情</p>
</footer>

</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"\n=== HTML 已生成: {output_path} ===")
    return full_html


# ============================================================
# 微信推送
# ============================================================
def push_wechat(news_data):
    sct_key = os.environ.get('SCT_KEY', '')
    if not sct_key:
        print("SCT_KEY not set, skipping push")
        return False

    site_url = os.environ.get('SITE_URL', 'https://global-win-news.github.io/trade-news/')

    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    date_str = now.strftime('%m月%d日')

    md = ''
    md += '## 📈 外贸重点\n'
    for item in news_data.get('trade', []):
        md += f"- {item['title']}\n"

    md += '\n## 🛒 跨境热点\n'
    for item in news_data.get('cross', []):
        md += f"- {item['title']}\n"

    md += '\n## 🌍 十大国际\n'
    for i, item in enumerate(news_data.get('intl', []), 1):
        md += f"{i}. {item['title']}\n"

    md += '\n## 🇨🇳 国内十大\n'
    for i, item in enumerate(news_data.get('domestic', []), 1):
        md += f"{i}. {item['title']}\n"

    md += f'\n---\n\n👉 [完整内容点击查看]({site_url})'

    try:
        resp = requests.post(
            f'https://sctapi.ftqq.com/{sct_key}.send',
            data={
                'title': f'📰 全球赢必看的新闻资讯 · {date_str}',
                'desp': md,
            },
            timeout=15
        )
        result = resp.json()
        if result.get('code') == 0:
            print(f"=== 微信推送成功! ===")
            return True
        else:
            print(f"=== 微信推送失败: {result} ===")
            return False
    except Exception as e:
        print(f"=== 微信推送异常: {e} ===")
        return False


# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print(f"运行时间: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}")

    # 收集新闻
    news = collect_news()

    # 生成 HTML
    output = os.environ.get('OUTPUT_PATH', 'index.html')
    generate_html(news, output)

    # 推送微信（仅当 PUSH_WECHAT=true 时）
    if os.environ.get('PUSH_WECHAT', '').lower() == 'true':
        print("\n=== 开始推送微信 ===")
        push_wechat(news)
    else:
        print("\n（PUSH_WECHAT 未设置，跳过微信推送）")

    print("\n=== 任务完成 ===")
