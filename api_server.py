#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat API HTTP 服务器（最简实现，用于演示完整 JSON 返回）。

使用方法：
    python api_server.py

然后访问：
    http://localhost:8000/chat?query=最近几年整体怎么样&birth_date=2005-09-20&birth_time=10:00&is_male=true&base_year=2025
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from bazi.compute_facts import compute_facts
from bazi.chat_api import chat_api
from bazi.request_index import generate_request_index
from bazi.extract_findings import extract_findings_from_facts
from bazi.year_detail import generate_year_detail

app = Flask(__name__)
CORS(app)  # 允许跨域请求


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """Chat API 端点。
    
    GET/POST 参数:
        query: 用户查询（必需）
        birth_date: 出生日期 YYYY-MM-DD（必需）
        birth_time: 出生时间 HH:MM（必需）
        is_male: 是否男性 true/false（必需）
        base_year: 服务器本地年份（可选，默认使用当前年份）
    """
    # 获取参数
    if request.method == 'GET':
        query = request.args.get('query', '')
        birth_date = request.args.get('birth_date', '')
        birth_time = request.args.get('birth_time', '')
        is_male_str = request.args.get('is_male', 'true').lower()
        base_year_str = request.args.get('base_year', '')
    else:  # POST
        data = request.get_json() if request.is_json else request.form
        query = data.get('query', '')
        birth_date = data.get('birth_date', '')
        birth_time = data.get('birth_time', '')
        is_male_str = data.get('is_male', 'true').lower()
        base_year_str = data.get('base_year', '')
    
    # 验证必需参数
    if not query or not birth_date or not birth_time:
        return jsonify({
            "answer": "",
            "index": {},
            "trace": {},
            "error": "Missing required parameters: query, birth_date, birth_time"
        }), 400
    
    # 解析参数
    try:
        is_male = is_male_str in ('true', '1', 'yes', 't')
        base_year = int(base_year_str) if base_year_str else None
        
        # 解析日期时间
        date_parts = birth_date.split("-")
        time_parts = birth_time.split(":")
        
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        birth_dt = datetime(year, month, day, hour, minute, 0)
        
        # 生成 facts（唯一真相源）
        facts = compute_facts(birth_dt, is_male, max_dayun=15)
        
        # 调用 Chat API
        response = chat_api(query, facts, base_year=base_year)
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "answer": "",
            "index": {},
            "trace": {},
            "error": str(e)
        }), 500


@app.route('/v1/analyze', methods=['POST'])
def analyze():
    """分析 API 端点（供 Next.js 前端调用）。
    
    POST JSON 参数:
        birth_date: 出生日期 YYYY-MM-DD（必需）
        birth_time: 出生时间 HH:MM（必需）
        is_male: 是否男性 true/false（必需）
        base_year: 服务器本地年份（可选，默认使用当前年份）
        target_year: 目标年份（可选，用于获取 year_detail）
    
    返回:
        {
            "index": { ... },
            "facts": { ... },
            "findings": { ... },
            "year_detail": { ... } | null,  # 如果指定了 target_year
            "error": null
        }
    """
    try:
        data = request.get_json() if request.is_json else {}
        birth_date = data.get('birth_date', '')
        birth_time = data.get('birth_time', '')
        is_male = data.get('is_male', True)
        base_year = data.get('base_year', datetime.now().year)
        target_year = data.get('target_year')  # 可选：目标年份
        
        # 验证必需参数
        if not birth_date or not birth_time:
            return jsonify({
                "index": {},
                "facts": {},
                "findings": {},
                "year_detail": None,
                "error": "Missing required parameters: birth_date, birth_time"
            }), 400
        
        # 解析日期时间
        date_parts = birth_date.split("-")
        time_parts = birth_time.split(":")
        
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        birth_dt = datetime(year, month, day, hour, minute, 0)
        
        # 生成 facts（唯一真相源）
        facts = compute_facts(birth_dt, is_male, max_dayun=15)
        
        # 生成 index
        index = generate_request_index(facts, base_year)
        
        # 生成 findings
        findings = extract_findings_from_facts(facts)
        
        # 如果指定了 target_year，生成 year_detail
        year_detail = None
        if target_year:
            year_detail = generate_year_detail(facts, int(target_year))
        
        return jsonify({
            "index": index,
            "facts": facts,
            "findings": findings,
            "year_detail": year_detail,
            "error": None
        })
        
    except Exception as e:
        return jsonify({
            "index": {},
            "facts": {},
            "findings": {},
            "year_detail": None,
            "error": str(e)
        }), 500


@app.route('/', methods=['GET'])
def index():
    """根路径，返回 API 使用说明。"""
    return """
    <h1>Chat API HTTP 服务器</h1>
    <h2>使用方法：</h2>
    <p>访问：<code>/chat?query=最近几年整体怎么样&birth_date=2005-09-20&birth_time=10:00&is_male=true&base_year=2025</code></p>
    <h2>参数说明：</h2>
    <ul>
        <li><code>query</code>: 用户查询（必需）</li>
        <li><code>birth_date</code>: 出生日期 YYYY-MM-DD（必需）</li>
        <li><code>birth_time</code>: 出生时间 HH:MM（必需）</li>
        <li><code>is_male</code>: 是否男性 true/false（必需）</li>
        <li><code>base_year</code>: 服务器本地年份（可选，默认使用当前年份）</li>
    </ul>
    <h2>示例：</h2>
    <ul>
        <li><a href="/chat?query=最近几年整体怎么样&birth_date=2005-09-20&birth_time=10:00&is_male=true&base_year=2025">最近几年整体怎么样</a></li>
        <li><a href="/chat?query=未来三年怎么样&birth_date=2005-09-20&birth_time=10:00&is_male=true&base_year=2025">未来三年怎么样</a></li>
        <li><a href="/chat?query=从今年开始第几年是好运&birth_date=2005-09-20&birth_time=10:00&is_male=true&base_year=2025">从今年开始第几年是好运</a></li>
    </ul>
    """


if __name__ == '__main__':
    print("=" * 80)
    print("Chat API HTTP 服务器启动")
    print("=" * 80)
    print("访问 http://localhost:5000/ 查看使用说明")
    print("访问 http://localhost:5000/chat?query=最近几年整体怎么样&birth_date=2005-09-20&birth_time=10:00&is_male=true&base_year=2025 测试 API")
    print("访问 http://localhost:5000/v1/analyze (POST) 获取 index/facts")
    print("=" * 80)
    app.run(host='0.0.0.0', port=5000, debug=True)

