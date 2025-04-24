#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube 쇼츠 키워드 빈도수 분석 모듈
크롤링된 데이터에서 키워드 빈도수를 분석하고 순위별로 저장
"""

import os
import json
import re
from collections import Counter
import datetime
from common.utils import save_results


def clean_text(text):
    """텍스트 정제: 특수문자 제거 및 소문자 변환"""
    if not text:
        return ""
    # 해시태그(#) 유지하면서 특수문자 제거
    text = re.sub(r'[^\w\s#가-힣ㄱ-ㅎㅏ-ㅣ]', ' ', text)
    # 불필요한 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def extract_hashtags(text):
    """텍스트에서 해시태그 추출"""
    if not text:
        return []
    hashtags = re.findall(r'#(\w+)', text)
    return [tag.lower() for tag in hashtags]


def extract_keywords(text, min_length=2):
    """텍스트에서 키워드 추출 (단어 및 구문)"""
    if not text:
        return []
    
    # 한글, 영문, 숫자 단어 추출 (최소 길이 이상)
    words = re.findall(r'[가-힣a-z0-9]+', text.lower())
    return [word for word in words if len(word) >= min_length]


def load_json_data(file_path):
    """
    JSON 파일에서 데이터 로드
    
    Args:
        file_path: 로드할 JSON 파일 경로
    
    Returns:
        dict 또는 list: 로드된 데이터
    """
    try:
        if file_path is None:
            raise ValueError("파일 경로가 None입니다.")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"파일 로드 중 오류 발생: {str(e)}")
        return None


def analyze_keyword_frequency(json_file, excluded_words=None, top_n=100, min_length=2):
    """
    JSON 파일에서 키워드 빈도수 분석
    
    Args:
        json_file (str): 분석할 JSON 파일 경로
        excluded_words (list): 제외할 단어 목록 (기본값: ["shorts", "shortsvideo"])
        top_n (int): 출력할 상위 키워드 수 (기본값: 100)
        min_length (int): 키워드 최소 길이 (기본값: 2)
    
    Returns:
        str: 결과 파일 경로
    """
    # 제외할 단어 기본값 설정
    if excluded_words is None:
        excluded_words = ["shorts", "shortsvideo", "short"]
    
    # 날짜 형식 추출
    today = datetime.datetime.now().strftime("%Y%m%d")
    
    try:
        # JSON 파일 로드
        data = load_json_data(json_file)
        if not data:
            return None
            
        # 데이터 형식 확인 (일반 목록 또는 중첩 구조)
        if isinstance(data, list):
            videos_data = data
        elif 'shorts' in data and isinstance(data['shorts'], list):
            videos_data = data['shorts']
        else:
            print("지원되지 않는 데이터 형식입니다.")
            return None
        
        print(f"분석 시작: {json_file}")
        print(f"총 {len(videos_data)} 개의 동영상 데이터 로드 완료")
        print(f"제외 단어: {', '.join(excluded_words)}")
        
        # 키워드 카운터 초기화
        all_keywords = Counter()
        hashtag_keywords = Counter()
        combined_keywords = Counter()  # 해시태그와 일반 키워드를 합친 카운터
        
        # 각 동영상 데이터 분석
        for video in videos_data:
            # 제목과 설명 결합
            title = clean_text(video.get('title', ''))
            description = clean_text(video.get('description', ''))
            combined_text = f"{title} {description}"
            
            # 해시태그 추출
            hashtags = extract_hashtags(combined_text)
            filtered_hashtags = [tag for tag in hashtags if tag not in excluded_words]
            hashtag_keywords.update(filtered_hashtags)
            
            # 일반 키워드 추출
            keywords = extract_keywords(combined_text, min_length)
            filtered_keywords = [keyword for keyword in keywords if keyword not in excluded_words]
            all_keywords.update(filtered_keywords)
            
            # 통합 키워드 업데이트 (해시태그와 일반 키워드 모두 포함)
            combined_keywords.update(filtered_hashtags)
            combined_keywords.update(filtered_keywords)
        
        # 문자열 길이순으로 정렬된 결과
        sorted_keywords = sorted(all_keywords.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
        sorted_hashtags = sorted(hashtag_keywords.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
        sorted_combined = sorted(combined_keywords.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
        
        # 결과 준비
        results = {
            "metadata": {
                "source_file": json_file,
                "analysis_date": today,
                "total_videos": len(videos_data),
                "excluded_words": excluded_words
            },
            "top_keywords": dict(sorted_keywords[:top_n]),
            "top_hashtags": dict(sorted_hashtags[:min(top_n, len(sorted_hashtags))]),
            "top_combined": dict(sorted_combined[:top_n])  # 통합 키워드 추가
        }
        
        # 상위 키워드 출력
        print(f"\n상위 10개 키워드:")
        for keyword, count in sorted_keywords[:10]:
            print(f"  - {keyword}: {count}회")
        
        print(f"\n상위 10개 해시태그:")
        for tag, count in sorted_hashtags[:10]:
            print(f"  - #{tag}: {count}회")
            
        print(f"\n상위 10개 통합 키워드 (해시태그 + 일반 키워드):")
        for keyword, count in sorted_combined[:10]:
            print(f"  - {keyword}: {count}회")
        
        # 파일명에서 키워드 추출 (youtube_동물_20250424.json -> 동물)
        try:
            search_keyword = os.path.basename(json_file).split('_')[1]
            output_target = f"analysis_{search_keyword}_frequency"
        except (IndexError, AttributeError):
            output_target = "analysis_frequency"
            
        # 결과 저장
        output_filename = save_results(output_target, results)
        
        return output_filename
        
    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")
        return None