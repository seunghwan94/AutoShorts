#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube 쇼츠 검색 엔진 - 핵심 모듈
검색 전략을 조율하고 결과를 수집하는 주요 로직
"""

import time
import random
from youtube.c_strategies import create_strategies, create_url
from youtube.d_page_parser import extract_shorts_from_page_with_token
from youtube.e_data_filters import filter_and_add_shorts, is_within_days

def get_shorts_by_keyword(keyword, min_views=100000, max_days=3, max_results=50):
    """
    키워드로 YouTube 쇼츠 데이터 추출 - 대폭 강화된 검색 전략 적용
    
    Args:
        keyword: 검색 키워드
        min_views: 최소 조회수 (기본값: 10만)
        max_days: 최근 며칠 이내의 쇼츠만 가져올지 (기본값: 3일)
        max_results: 가져올 최대 결과 수 (기본값: 50개)
    """
    filtered_shorts = []  # 조회수와 날짜 필터를 모두 통과한 결과
    existing_ids = set()  # 중복 추적
    
    # 검색 효율을 위한 추적
    processed_urls = set()  # 이미 검색한 URL
    discovered_channels = {}  # 발견된 채널 {id: {name, video_count}}
    
    print(f"'{keyword}' 키워드로 YouTube 쇼츠 데이터 추출 시작...")
    print(f"필터: 최근 {max_days}일 이내 + 조회수 {min_views:,}회 이상")
    print(f"목표: {max_results}개 수집")
    
    # 전략 1: 다양한 검색 매개변수 및 키워드 조합 활용
    search_strategies = create_strategies(keyword)
    
    # 검색 루프
    strategy_index = 0
    max_strategies = len(search_strategies)
    max_search_depth = 5  # 검색 깊이 제한 (더 깊게 검색)
    
    while len(filtered_shorts) < max_results and strategy_index < max_strategies:
        current_strategy = search_strategies[strategy_index]
        url = current_strategy["url"]
        description = current_strategy["description"]
        
        # 이미 처리한 URL은 건너뛰기
        if url in processed_urls:
            strategy_index += 1
            continue
            
        processed_urls.add(url)
        print(f"\n전략 {strategy_index+1}/{max_strategies}: {description}")
        print(f"URL: {url}")
        
        # 페이지 데이터 가져오기
        shorts_from_url, next_token = extract_shorts_from_page_with_token(url)
        
        if not shorts_from_url:
            print("이 전략에서 데이터를 찾지 못했습니다.")
            strategy_index += 1
            continue
            
        print(f"검색 결과: {len(shorts_from_url)}개 쇼츠 발견")
        
        # 필터링 및 중복 제거
        filtered_count = filter_and_add_shorts(shorts_from_url, filtered_shorts, existing_ids, min_views, max_days)
        print(f"필터 통과: {filtered_count}개 (누적 {len(filtered_shorts)}개/{max_results}개)")
        
        # 채널 정보 수집 (후속 검색용)
        for short in shorts_from_url:
            channel_id = short.get("channel_id")
            channel_name = short.get("channel_name")
            if channel_id and channel_name and channel_id not in discovered_channels:
                discovered_channels[channel_id] = {
                    "name": channel_name, 
                    "video_count": 1
                }
            elif channel_id in discovered_channels:
                discovered_channels[channel_id]["video_count"] += 1
        
        # 전략 2: 연속 토큰을 사용하여 더 많은 결과 로드 (YouTube 무한 스크롤 시뮬레이션)
        depth = 0
        while next_token and len(filtered_shorts) < max_results and depth < max_search_depth:
            depth += 1
            print(f"  ↳ 연속 페이지 {depth}/{max_search_depth} 로드 중...")
            
            # 페이지 사이 짧은 딜레이
            time.sleep(random.uniform(1.5, 3.0))
            
            # 연속 토큰으로 다음 페이지 로드
            next_url = create_url(url, next_token)
            more_shorts, next_token = extract_shorts_from_page_with_token(next_url)
            
            if not more_shorts:
                print("  ↳ 더 이상 결과가 없습니다.")
                break
                
            print(f"  ↳ {len(more_shorts)}개 추가 쇼츠 발견")
            
            # 필터링 및 중복 제거
            filtered_count = filter_and_add_shorts(more_shorts, filtered_shorts, existing_ids, min_views, max_days)
            print(f"  ↳ 필터 통과: {filtered_count}개 (누적 {len(filtered_shorts)}개/{max_results}개)")
            
            # 채널 정보 수집 (후속 검색용)
            for short in more_shorts:
                channel_id = short.get("channel_id")
                channel_name = short.get("channel_name")
                if channel_id and channel_name and channel_id not in discovered_channels:
                    discovered_channels[channel_id] = {
                        "name": channel_name, 
                        "video_count": 1
                    }
                elif channel_id in discovered_channels:
                    discovered_channels[channel_id]["video_count"] += 1
        
        # 다음 전략으로 이동
        strategy_index += 1
        
        # 충분한 결과를 얻으면 중단
        if len(filtered_shorts) >= max_results:
            break
    
    # 전략 4: 조회수 필터 동적 조정 (결과가 매우 부족한 경우에만)
    if len(filtered_shorts) < max_results * 0.3:  # 목표의 30% 미만
        print(f"\n결과가 너무 적습니다 ({len(filtered_shorts)}개/{max_results}개). 조회수 기준을 일시적으로 낮춰 추가 검색을 시도합니다...")
        
        # 조회수 기준 낮추기 (원래의 50%)
        adjusted_min_views = min_views // 2
        print(f"조회수 임계값 조정: {min_views:,} → {adjusted_min_views:,}")
        
        # 이미 처리된 URL 재사용 (다른 조회수 기준으로)
        original_size = len(filtered_shorts)
        
        for url in list(processed_urls)[:10]:  # 처음 10개 URL만 재시도
            if len(filtered_shorts) >= max_results:
                break
                
            print(f"URL 재시도 (낮은 조회수 기준): {url}")
            shorts_from_url, _ = extract_shorts_from_page_with_token(url)
            
            if not shorts_from_url:
                continue
                
            # 낮은 조회수 기준으로 필터링
            for short in shorts_from_url:
                video_id = short.get("video_id", "")
                
                # 중복 건너뛰기
                if video_id in existing_ids:
                    continue
                    
                # ID 추적에 추가
                existing_ids.add(video_id)
                
                # 시간 필터
                if not is_within_days(short.get("published_time", ""), max_days):
                    continue
                    
                # 조정된 조회수 필터
                views = short.get("views", 0)
                if views < adjusted_min_views:
                    continue
                    
                # 필터를 통과한 결과 추가
                filtered_shorts.append(short)
                
                # 목표 달성시 중단
                if len(filtered_shorts) >= max_results:
                    break
            
            time.sleep(random.uniform(1.0, 2.0))
        
        added = len(filtered_shorts) - original_size
        print(f"조회수 기준 조정으로 {added}개 추가 데이터 확보 (총 {len(filtered_shorts)}개)")
    




    # 최종 메시지
    if len(filtered_shorts) >= max_results:
        print(f"\n✅ 목표 달성! {max_results}개의 필터링된 쇼츠를 찾았습니다.")
    else:
        print(f"\n⚠️ 최대한의 노력을 했으나 목표인 {max_results}개보다 적은 {len(filtered_shorts)}개만 찾았습니다.")
        print("조건을 충족하는 쇼츠가 충분하지 않은 것 같습니다.")
    
    # 조회수 기준 정렬
    filtered_shorts.sort(key=lambda x: x.get("views", 0), reverse=True)
    
    return filtered_shorts