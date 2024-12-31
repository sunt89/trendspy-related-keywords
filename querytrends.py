from trendspy import Trends
import pandas as pd
import json
import time
import random
from datetime import datetime
import backoff  
from config import TRENDS_CONFIG
import requests
from urllib.parse import quote
import re

def get_google_nid():
    """
    自动获取Google NID cookie
    """
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        # 访问Google主页获取初始cookie
        response = session.get('https://www.google.com/', headers=headers)
        response.raise_for_status()
        
        # 从响应中提取NID
        cookies = session.cookies.get_dict()
        nid = cookies.get('NID')
        
        if nid:
            return nid
        
        # 如果没有直接获取到NID，尝试从搜索页面获取
        search_term = quote('test')
        response = session.get(f'https://www.google.com/search?q={search_term}', headers=headers)
        response.raise_for_status()
        
        cookies = session.cookies.get_dict()
        nid = cookies.get('NID')
        
        if nid:
            return nid
            
        # 如果还是没有获取到，从响应内容中尝试提取
        match = re.search(r'NID=([^;]+)', response.text)
        if match:
            return match.group(1)
            
        return None
    except Exception as e:
        print(f"获取NID失败: {str(e)}")
        return None

@backoff.on_exception(
    backoff.expo,  # 指数退避策略
    Exception,     # 捕获所有异常
    max_tries=5    # 最大重试次数
)
def get_related_queries(keyword, geo='', timeframe='today 12-m'):
    """
    获取关键词的相关查询数据，带重试机制和请求限制
    """
    tr = Trends(hl='zh-CN')
    
    # 随机化 User-Agent
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'referer': 'https://www.google.com/',
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    # 尝试从配置获取NID，如果没有则自动获取
    nid = TRENDS_CONFIG.get('nid')
    if not nid:
        nid = get_google_nid()
        if nid:
            print("成功自动获取NID")
    
    if nid:
        headers['Cookie'] = f'NID={nid}'
    
    try:
        # 检查请求限制
        request_limiter.wait_if_needed()
        
        # 添加随机延时
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        related_data = tr.related_queries(
            keyword,
            headers=headers,
            geo=geo,
            timeframe=timeframe
        )
        return related_data
        
    except Exception as e:
        print(f"尝试获取数据时出错: {str(e)}")
        raise

def batch_get_queries(keywords, geo='', timeframe='today 12-m', delay_between_queries=5):
    """
    批量获取多个关键词的数据，带间隔控制
    """
    results = {}
    
    for keyword in keywords:
        try:
            print(f"\n正在查询关键词: {keyword}")
            results[keyword] = get_related_queries(keyword, geo, timeframe)
            
            # 在请求之间添加延时
            if keyword != keywords[-1]:  # 如果不是最后一个关键词
                delay = delay_between_queries + random.uniform(0, 2)
                print(f"等待 {delay:.1f} 秒后继续下一个查询...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"获取 {keyword} 的数据失败: {str(e)}")
            results[keyword] = None
            
            # 如果遇到错误，增加额外等待时间
            time.sleep(10)
    
    return results

def save_related_queries(keyword, related_data):
    """
    保存相关查询数据到JSON文件
    """
    if not related_data:
        return
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    json_data = {
        'keyword': keyword,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'related_queries': {
            'top': related_data['top'].to_dict(orient='records') if isinstance(related_data.get('top'), pd.DataFrame) else related_data.get('top'),
            'rising': related_data['rising'].to_dict(orient='records') if isinstance(related_data.get('rising'), pd.DataFrame) else related_data.get('rising')
        }
    }
    
    # 保存为JSON文件
    filename = f"related_queries_{keyword}_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    return filename

def print_related_queries(related_data):
    """
    打印相关查询词数据
    """
    if not related_data:
        print("没有相关查询数据")
        return
    
    print("\n相关查询词统计:")
    print("=" * 50)
    
    # 打印热门查询
    if 'top' in related_data and related_data['top'] is not None:
        print("\n热门查询:")
        print("-" * 30)
        df = related_data['top']
        if isinstance(df, pd.DataFrame):
            for _, row in df.iterrows():
                print(f"- {row['query']:<30} (相关度: {row['value']})")
    
    # 打印上升趋势查询
    if 'rising' in related_data and related_data['rising'] is not None:
        print("\n上升趋势查询:")
        print("-" * 30)
        df = related_data['rising']
        if isinstance(df, pd.DataFrame):
            for _, row in df.iterrows():
                print(f"- {row['query']:<30} (增长: {row['value']})")


# 主函数
# timeframe可能的值：
# today 12-m：12个月
# now 1-d：1天
# now 7-d：7天
# now 30-d：30天
# now 90-d：90天
# 日期格式：2024-12-28 2024-12-30
def main():
    # 设置要查询的关键词列表
    keywords = ['game']  # 可以添加多个关键词
    geo = ''
    timeframe = 'now 1-d'
    
    print("开始批量查询...")
    print(f"地区: {geo if geo else '全球'}")
    print(f"时间范围: {timeframe}")
    
    try:
        # 批量获取数据
        results = batch_get_queries(
            keywords,
            geo=geo,
            timeframe=timeframe,
            delay_between_queries=5  # 设置请求间隔
        )
        
        # 处理和保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        for keyword, data in results.items():
            if data:
                print(f"\n处理 {keyword} 的数据:")
                print_related_queries(data)
                filename = save_related_queries(keyword, data)
                print(f"数据已保存到文件: {filename}")
            else:
                print(f"\n未能获取 {keyword} 的数据")
                
    except Exception as e:
        print(f"批量查询过程中出错: {str(e)}")

class RequestLimiter:
    def __init__(self):
        self.requests = []  # 存储请求时间戳
        self.max_requests_per_min = 30  # 每分钟最大请求数
        self.max_requests_per_hour = 200  # 每小时最大请求数
        
    def can_make_request(self):
        """检查是否可以发起新请求"""
        current_time = time.time()
        
        # 清理超过1小时的旧请求记录
        self.requests = [t for t in self.requests if current_time - t < 3600]
        
        # 获取最近1分钟的请求数
        recent_min_requests = len([t for t in self.requests if current_time - t < 60])
        
        # 获取最近1小时的请求数
        recent_hour_requests = len(self.requests)
        
        if (recent_min_requests >= self.max_requests_per_min or 
            recent_hour_requests >= self.max_requests_per_hour):
            return False
        
        return True
    
    def add_request(self):
        """记录新的请求"""
        self.requests.append(time.time())
    
    def wait_if_needed(self):
        """如果需要，等待直到可以发送请求"""
        while not self.can_make_request():
            wait_time = random.uniform(5, 10)
            print(f"达到请求限制，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
        self.add_request()

# 创建全局请求限制器
request_limiter = RequestLimiter()

if __name__ == "__main__":
    main()
