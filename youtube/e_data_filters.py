#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube 쇼츠 데이터 필터링 모듈
조회수 및 날짜 기반 필터링, 중복 제거
"""

import re
from datetime import datetime, timedelta

def is_within_days(time_text, days=3):
    """
    게시 시간이 지정된 일수 이내인지 확인
    """
    if not time_text:
        return False
    
    # "N일 전" 패턴
    day_match = re.search(r'(\d+)\s*일\s*전', time_text)
    if day_match:
        days_ago = int(day_match.group(1))
        return days_ago <= days
    
    # "N days ago" 패턴 (영어)
    day_en_match = re.search(r'(\d+)\s*days?\s*ago', time_text, re.IGNORECASE)
    if day_en_match:
        days_ago = int(day_en_match.group(1))
        return days_ago <= days
    
    # 시간, 분, 초 전은 항상 최근
    if re.search(r'시간\s*전|분\s*전|초\s*전|방금', time_text, re.IGNORECASE):
        return True
    
    # "어제", "오늘", "yesterday", "today"는 최근
    if re.search(r'어제|오늘|yesterday|today', time_text, re.IGNORECASE):
        return True
    
    # "N주 전", "N weeks ago" 패턴은 명시적으로 거부
    if re.search(r'\d+\s*주\s*전|\d+\s*weeks?\s*ago', time_text, re.IGNORECASE):
        return False
    
    # "N개월 전", "N months ago" 패턴은 명시적으로 거부
    if re.search(r'\d+\s*(?:개월|달)\s*전|\d+\s*months?\s*ago', time_text, re.IGNORECASE):
        return False
    
    # "N년 전", "N years ago" 패턴은 명시적으로 거부
    if re.search(r'\d+\s*년\s*전|\d+\s*years?\s*ago', time_text, re.IGNORECASE):
        return False
    
    # 특정 날짜 형식 (예: "2023년 10월 15일")
    date_match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', time_text)
    if date_match:
        year = int(date_match.group(1))
        month = int(date_match.group(2))
        day = int(date_match.group(3))
        
        # 현재 날짜와 비교
        now = datetime.now()
        video_date = datetime(year, month, day)
        delta = now - video_date
        
        return delta.days <= days
    
    # 기본적으로 확인할 수 없는 형식은 거부
    return False

def filter_and_add_shorts(shorts_list, filtered_results, existing_ids, min_views, max_days):
    """쇼츠 데이터를 필터링하고 결과 목록에 추가"""
    added_count = 0
    
    for short in shorts_list:
        video_id = short.get("video_id", "")
        
        # 중복 건너뛰기
        if video_id in existing_ids:
            continue
            
        # ID 추적에 추가
        existing_ids.add(video_id)
        
        # 시간 필터
        if not is_within_days(short.get("published_time", ""), max_days):
            continue
            
        # 조회수 필터
        views = short.get("views", 0)
        if views < min_views:
            continue
            
        # 두 필터를 모두 통과한 결과만 추가
        filtered_results.append(short)
        added_count += 1
    
    return added_count