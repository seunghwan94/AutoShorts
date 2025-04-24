#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube 쇼츠 검색 전략 모듈
검색 URL 생성 및 관리
"""
from urllib.parse import quote, parse_qs, urlparse
import time
import requests
import json
import re

def create_strategies(keyword):
    """다양한 검색 전략 생성"""
    strategies = []
    encoded_keyword = quote(keyword)
    
    # 1. 기본 검색 URL
    base_strategies = [
        {
            "url": f"https://www.youtube.com/results?search_query={encoded_keyword}+shorts&sp=CAMSAhAB",
            "description": f"'{keyword}' + shorts (인기순 정렬)"
        },
        {
            "url": f"https://www.youtube.com/results?search_query={encoded_keyword}+shorts&sp=CAISAhAB",
            "description": f"'{keyword}' + shorts (최신순 정렬)"
        },
        {
            "url": f"https://www.youtube.com/results?search_query={encoded_keyword}+shorts&sp=CAASAhAB",
            "description": f"'{keyword}' + shorts (조회순 정렬)"
        },
        {
            "url": f"https://www.youtube.com/results?search_query={encoded_keyword}&sp=EgIYAQ%253D%253D",
            "description": f"'{keyword}' (쇼츠 필터)"
        },
        {
            "url": f"https://www.youtube.com/results/search?q={encoded_keyword}",
            "description": f"쇼츠 직접 검색 '{keyword}'"
        }
    ]

    strategies.extend(base_strategies)

    # 2. 연관 검색어 가져오기
    related_keywords = get_related_keywords(keyword)

    # 연관 검색어 기반 전략 추가 (기본 검색과 동일한 방식으로)
    for related in related_keywords:
        encoded_related = quote(related)
        # 연관 검색어에 대해 기본 검색과 동일한 전략 적용
        related_strategies = [
            # {
            #     "url": f"https://www.youtube.com/results?search_query={encoded_related}+shorts&sp=CAMSAhAB",
            #     "description": f"연관검색어 '{related}' + shorts (인기순 정렬)"
            # },
            # {
            #     "url": f"https://www.youtube.com/results?search_query={encoded_related}+shorts&sp=CAISAhAB", 
            #     "description": f"연관검색어 '{related}' + shorts (최신순 정렬)"
            # },
            # {
            #     "url": f"https://www.youtube.com/results?search_query={encoded_related}+shorts&sp=CAASAhAB",
            #     "description": f"연관검색어 '{related}' + shorts (조회순 정렬)"
            # },
            # {
            #     "url": f"https://www.youtube.com/results?search_query={encoded_related}&sp=EgIYAQ%253D%253D",
            #     "description": f"연관검색어 '{related}' (쇼츠 필터)"
            # },
            # {
            #     "url": f"https://www.youtube.com/results/search?q={encoded_related}",
            #     "description": f"연관검색어 쇼츠 직접 검색 '{related}'"
            # }
        ]
        strategies.extend(related_strategies)
        
        # 4. 해시태그 검색
        strategies.append({
            "url": f"https://www.youtube.com/hashtag/{encoded_keyword}",
            "description": f"해시태그 #{keyword}"
        })
        
        # 5. 기간 필터 추가
        strategies.append({
            "url": f"https://www.youtube.com/results?search_query={encoded_keyword}+shorts&sp=EgIIAw%253D%253D",
            "description": f"'{keyword}' + shorts (오늘 업로드)"
        })
        
        strategies.append({
            "url": f"https://www.youtube.com/results?search_query={encoded_keyword}+shorts&sp=EgQIAhAB",
            "description": f"'{keyword}' + shorts (이번 주 업로드)"
        })
        
    return strategies

def create_url(original_url, token):
    """연속 토큰을 사용하여 다음 페이지 URL 생성"""
    # YouTube API 키 추출 (또는 기본값 사용)
    api_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    
    parsed_url = urlparse(original_url)
    query_params = parse_qs(parsed_url.query)
    
    # URL에서 API 키 추출 시도
    if "key" in query_params and query_params["key"][0]:
        api_key = query_params["key"][0]
    
    # 연속 URL 생성
    continuation_url = f"https://www.youtube.com/browse_ajax?ctoken={token}&continuation={token}&key={api_key}"
    return continuation_url

def get_related_keywords(keyword):
    """YouTube 검색창의 자동완성 검색어(연관 검색어) 가져오기"""
    try:
        # 검색어 인코딩
        encoded_keyword = quote(keyword)
        
        # YouTube 자동완성 API URL (변경된 엔드포인트)
        url = f"https://suggestqueries-clients6.youtube.com/complete/search?client=youtube&hl=ko&gl=kr&ds=yt&q={encoded_keyword}&callback=google.sbox.p50"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.youtube.com/"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            # JSONP 형식에서 JSON 부분만 추출 (callback 함수 제거)
            content = response.text
            json_str = re.search(r'google\.sbox\.p50\((.*?)\)', content)
            
            if json_str:
                data = json.loads(json_str.group(1))
                
                # YouTube 자동완성 검색어 추출
                suggestions = []
                if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                    for item in data[1]:
                        if isinstance(item, list) and len(item) > 0:
                            suggestion = item[0]
                            if suggestion.lower() != keyword.lower():
                                suggestions.append(suggestion)
                
                if suggestions:
                    print(f"성공적으로 {len(suggestions)}개의 연관 검색어를 가져왔습니다.")
                    return suggestions
                    
        # 두 번째 방법: 구글 자동완성 API 시도
        google_url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={encoded_keyword}"
        response = requests.get(google_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = [item for item in data[1] if item.lower() != keyword.lower()]
            
            if suggestions:
                print(f"구글 API에서 {len(suggestions)}개의 연관 검색어를 가져왔습니다.")
                print("연관 검색어:", suggestions)
                return suggestions
    
    except Exception as e:
        print(f"연관 검색어 가져오기 실패: {e}")

    return []

def extract_text(text_container):
    """텍스트 컨테이너에서 텍스트 추출"""
    if not text_container:
        return ""
    
    if "simpleText" in text_container:
        return text_container["simpleText"]
    elif "runs" in text_container:
        return "".join([run.get("text", "") for run in text_container["runs"]])
    
    return ""