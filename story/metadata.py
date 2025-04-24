#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
메타데이터 생성 모듈
스토리 기반의 제목 및 해시태그 생성 최적화 기능
"""

import os
import re
import sys
import json
import logging
import random
from typing import Dict, List, Any, Optional, Tuple

# 상위 디렉토리 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from story.llm import llm_provider
from story.prompt import get_title_prompt, get_hashtags_prompt

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetadataGenerator:
    """제목 및 해시태그 생성 클래스"""
    
    def __init__(self):
        """메타데이터 생성기 초기화"""
        self.llm = llm_provider
        logger.info("메타데이터 생성기 초기화 완료")
        
        # 인기 있는 해시태그 (클릭률 향상용)
        self.popular_hashtags = [
            "#레전드썰", "#실화썰", "#공감썰", "#경악썰", "#충격썰",
            "#인생썰", "#사연", "#일상", "#공감", "#중년", 
            "#50대", "#40대", "#60대", "#썰전", "#인간관계",
            "#가족", "#이웃", "#아파트", "#결혼", "#직장",
            "#돈", "#상속", "#건강", "#시어머니", "#며느리"
        ]
    
    def optimize_title(self, story: str, keyword: str, raw_title: str = None) -> str:
        """
        스토리 기반으로 최적화된 제목 생성
        
        Args:
            story: 생성된 스토리 내용
            keyword: 원본 키워드
            raw_title: 이미 생성된 제목 (있는 경우 개선)
            
        Returns:
            최적화된 제목
        """
        try:
            # 이미 생성된 제목이 있으면 최적화만 수행
            if raw_title:
                return self._refine_title(raw_title, keyword)
            
            # 새 제목 생성
            prompt = get_title_prompt(story, keyword)
            title = self.llm.generate_text(prompt, max_tokens=50, temperature=0.8)
            
            if not title:
                logger.warning("제목 생성 실패, 기본 제목 사용")
                return f"{keyword} 관련 레전드 썰"
            
            # 제목 최적화
            return self._refine_title(title, keyword)
            
        except Exception as e:
            logger.error(f"제목 최적화 중 오류 발생: {str(e)}")
            return f"{keyword} 관련 레전드 썰"
    
    def optimize_hashtags(self, story: str, title: str, keyword: str, raw_hashtags: str = None) -> str:
        """
        스토리와 제목 기반으로 최적화된 해시태그 생성
        
        Args:
            story: 생성된 스토리 내용
            title: 생성된 제목
            keyword: 원본 키워드
            raw_hashtags: 이미 생성된 해시태그 (있는 경우 개선)
            
        Returns:
            최적화된 해시태그 문자열
        """
        try:
            # 이미 생성된 해시태그가 있으면 최적화만 수행
            if raw_hashtags:
                return self._refine_hashtags(raw_hashtags, keyword, title)
            
            # 새 해시태그 생성
            prompt = get_hashtags_prompt(story, title, keyword)
            hashtags = self.llm.generate_text(prompt, max_tokens=100, temperature=0.7)
            
            if not hashtags:
                logger.warning("해시태그 생성 실패, 기본 해시태그 사용")
                return self._generate_default_hashtags(keyword)
            
            # 해시태그 최적화
            return self._refine_hashtags(hashtags, keyword, title)
            
        except Exception as e:
            logger.error(f"해시태그 최적화 중 오류 발생: {str(e)}")
            return self._generate_default_hashtags(keyword)
    
    def _refine_title(self, title: str, keyword: str) -> str:
        """
        제목 정제 및 최적화
        
        Args:
            title: 원본 제목
            keyword: 원본 키워드
            
        Returns:
            정제된 제목
        """
        # 줄바꿈 및 여분의 공백 제거
        title = re.sub(r'\s+', ' ', title).strip()
        
        # 따옴표 제거
        title = title.replace('"', '').replace("'", '')
        
        # 제목이 너무 길면 자르기 (35자 제한)
        if len(title) > 35:
            title = title[:32] + "..."
            
        # 제목에 키워드가 없으면 추가
        if keyword not in title and len(title) + len(keyword) + 3 <= 35:
            title = f"{keyword} {title}"
            
        # '썰'이 없으면 추가
        if "썰" not in title and len(title) + 3 <= 35:
            title = f"{title} 썰"
            
        # 감정적 표현 추가 (공간이 있는 경우)
        emotional_markers = ["ㄷㄷ", "충격", "경악", "헉"]
        if len(title) <= 30 and not any(em in title for em in emotional_markers):
            marker = random.choice(emotional_markers)
            title = f"{title} {marker}"
            
        return title
    
    def _refine_hashtags(self, hashtags: str, keyword: str, title: str) -> str:
        """
        해시태그 정제 및 최적화
        
        Args:
            hashtags: 원본 해시태그 문자열
            keyword: 원본 키워드
            title: 생성된 제목
            
        Returns:
            정제된 해시태그 문자열
        """
        # 해시태그 분리
        if not hashtags.startswith('#'):
            # '#' 기호가 없는 경우 처리
            hashtags = ' '.join([f"#{tag.strip()}" for tag in hashtags.split() if tag.strip()])
        
        # 모든 해시태그 추출
        tags = re.findall(r'#\w+', hashtags.replace(' ', ''))
        
        # 중복 제거
        unique_tags = list(dict.fromkeys(tags))
        
        # 키워드 기반 해시태그 추가
        # 쉼표로 구분된 여러 키워드 처리
        if ',' in keyword:
            keywords = [k.strip() for k in keyword.split(',')]
            for kw in keywords:
                keyword_tag = f"#{kw.replace(' ', '')}"
                if keyword_tag not in unique_tags:
                    unique_tags.append(keyword_tag)
        else:
            keyword_tag = f"#{keyword.replace(' ', '')}"
            if keyword_tag not in unique_tags:
                unique_tags.append(keyword_tag)
            
        # 썰 관련 태그 추가
        if "#레전드썰" not in unique_tags:
            unique_tags.append("#레전드썰")
        if "#실화썰" not in unique_tags:
            unique_tags.append("#실화썰")
            
        # 제목에서 핵심 키워드 추출해 태그로 추가
        title_words = [w for w in re.findall(r'\w+', title) if len(w) >= 2]
        for word in title_words[:2]:  # 상위 2개만 사용
            tag = f"#{word}"
            if tag not in unique_tags:
                unique_tags.append(tag)
                
        # 인기 해시태그 몇 개 추가
        current_count = len(unique_tags)
        if current_count < 10:
            # 추가할 인기 태그 수
            to_add = min(10 - current_count, 3)
            # 아직 포함되지 않은 인기 태그 필터링
            available_popular = [t for t in self.popular_hashtags if t not in unique_tags]
            # 랜덤하게 선택하여 추가
            for tag in random.sample(available_popular, min(to_add, len(available_popular))):
                unique_tags.append(tag)
        
        # 최대 10개로 제한
        if len(unique_tags) > 10:
            unique_tags = unique_tags[:10]
            
        # 공백으로 구분하여 반환
        return ' '.join(unique_tags)
    
    def _generate_default_hashtags(self, keyword: str) -> str:
        """
        기본 해시태그 생성
        
        Args:
            keyword: 원본 키워드
            
        Returns:
            기본 해시태그 문자열
        """
        # 쉼표로 구분된 여러 키워드 처리
        keyword_tags = []
        if ',' in keyword:
            keywords = [k.strip() for k in keyword.split(',')]
            for kw in keywords:
                keyword_tags.append(f"#{kw.replace(' ', '')}")
        else:
            keyword_tags.append(f"#{keyword.replace(' ', '')}")
        
        basic_tags = ["#레전드썰", "#실화썰", "#공감썰", "#인생썰", "#경험담", "#사연", "#일상", "#공감"]
        
        # 키워드 태그를 맨 앞에 추가
        all_tags = keyword_tags + basic_tags
        
        # 최대 10개로 제한
        if len(all_tags) > 10:
            all_tags = all_tags[:10]
            
        return ' '.join(all_tags)

# 싱글톤 인스턴스 생성
metadata_generator = MetadataGenerator()

def optimize_title(story: str, keyword: str, raw_title: str = None) -> str:
    """
    스토리 기반으로 최적화된 제목 생성 (편의 함수)
    
    Args:
        story: 생성된 스토리 내용
        keyword: 원본 키워드
        raw_title: 이미 생성된 제목 (있는 경우 개선)
        
    Returns:
        최적화된 제목
    """
    return metadata_generator.optimize_title(story, keyword, raw_title)

def optimize_hashtags(story: str, title: str, keyword: str, raw_hashtags: str = None) -> str:
    """
    스토리와 제목 기반으로 최적화된 해시태그 생성 (편의 함수)
    
    Args:
        story: 생성된 스토리 내용
        title: 생성된 제목
        keyword: 원본 키워드
        raw_hashtags: 이미 생성된 해시태그 (있는 경우 개선)
        
    Returns:
        최적화된 해시태그 문자열
    """
    return metadata_generator.optimize_hashtags(story, title, keyword, raw_hashtags)