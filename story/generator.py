#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
스토리 생성 모듈
키워드를 입력받아 LLM을 통해 스토리, 제목, 해시태그, 생성
"""

import os
import json
import time
import logging
import sys
import traceback
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 상위 디렉토리 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from story.llm import llm_provider
from story.prompt import get_story_prompt, get_story_prompt_multi_keywords, get_title_prompt, get_hashtags_prompt

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StoryGenerator:
    """스토리 생성 클래스"""
    
    def __init__(self):
        """스토리 생성기 초기화"""
        self.llm = llm_provider
        logger.info("스토리 생성기 초기화 완료")
        
        # 결과 저장 디렉토리 확인
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    def create_story_from_keyword(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        키워드로부터 스토리, 제목, 해시태그 생성
        
        Args:
            keyword: 스토리 생성에 사용할 키워드
            
        Returns:
            생성된 콘텐츠를 담은 딕셔너리 또는 None
        """
        try:
            logger.info(f"'{keyword}' 키워드로 스토리 생성 시작")
            
            # 1. 스토리 생성
            story_prompt = get_story_prompt(keyword)
            story = self.llm.generate_text(story_prompt)
            
            if not story:
                logger.error(f"'{keyword}' 스토리 생성 실패")
                return None
                
            logger.info(f"스토리 생성 완료: {len(story)} 글자")
            
            # 2. 제목 생성
            title_prompt = get_title_prompt(story, keyword)
            title = self.llm.generate_text(title_prompt, max_tokens=50, temperature=0.8)
            
            if not title:
                logger.warning(f"'{keyword}' 제목 생성 실패, 기본 제목 사용")
                title = f"{keyword} 관련 레전드 썰"
                
            logger.info(f"제목 생성 완료: {title}")
            
            # 3. 해시태그 생성
            hashtags_prompt = get_hashtags_prompt(story, title, keyword)
            hashtags = self.llm.generate_text(hashtags_prompt, max_tokens=100, temperature=0.7)
            
            if not hashtags:
                logger.warning(f"'{keyword}' 해시태그 생성 실패, 기본 해시태그 사용")
                hashtags = f"#레전드썰 #{keyword}썰 #실화썰 #공감썰 #중년썰 #인생썰 #경험담 #사연 #일상 #공감"
                
            logger.info(f"해시태그 생성 완료: {hashtags}")
            
            # 결과 반환
            result = {
                "keyword": keyword,
                "story": story,
                "title": title,
                "hashtags": hashtags,
                "created_at": datetime.now().isoformat(),
                "model": config.LLM_MODEL
            }
            
            # 결과 저장
            self._save_story(result)
            
            return result
            
        except Exception as e:
            logger.error(f"스토리 생성 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())  # 스택 트레이스 로깅 추가
            return None
    
    def create_story_from_multiple_keywords(self, keywords: List[str]) -> Optional[Dict[str, Any]]:
        """
        여러 키워드를 모두 포함하는 하나의 스토리 생성
        
        Args:
            keywords: 스토리 생성에 사용할 키워드 목록
            
        Returns:
            생성된 콘텐츠를 담은 딕셔너리 또는 None
        """
        try:
            combined_keyword = ", ".join(keywords)
            logger.info(f"여러 키워드({combined_keyword})로 통합 스토리 생성 시작")
            
            # 1. 스토리 생성
            story_prompt = get_story_prompt_multi_keywords(keywords)
            story = self.llm.generate_text(story_prompt)
            
            if not story:
                logger.error(f"'{combined_keyword}' 스토리 생성 실패")
                return None
                
            logger.info(f"통합 스토리 생성 완료: {len(story)} 글자")
            
            # 2. 제목 생성
            title_prompt = get_title_prompt(story, combined_keyword)
            title = self.llm.generate_text(title_prompt, max_tokens=50, temperature=0.8)
            
            if not title:
                logger.warning(f"'{combined_keyword}' 제목 생성 실패, 기본 제목 사용")
                # 주제 변수 대신 keywords의
                first_keywords = ' '.join(keywords[:2])
                title = f"{first_keywords} 관련 레전드 썰"
                
            logger.info(f"제목 생성 완료: {title}")
            
            # 3. 해시태그 생성
            hashtags_prompt = get_hashtags_prompt(story, title, combined_keyword)
            hashtags = self.llm.generate_text(hashtags_prompt, max_tokens=100, temperature=0.7)
            
            if not hashtags:
                logger.warning(f"'{combined_keyword}' 해시태그 생성 실패, 기본 해시태그 사용")
                # 기본 해시태그 생성 (모든 키워드 포함)
                keyword_tags = ' '.join([f"#{kw.strip()}" for kw in keywords])
                hashtags = f"{keyword_tags} #레전드썰 #실화썰 #공감썰 #중년썰 #인생썰"
                
            logger.info(f"해시태그 생성 완료: {hashtags}")
            
            # 결과 반환
            result = {
                "keyword": combined_keyword,
                "keywords": keywords,
                "story": story,
                "title": title,
                "hashtags": hashtags,
                "created_at": datetime.now().isoformat(),
                "model": config.LLM_MODEL
            }
            
            # 결과 저장
            self._save_story(result)
            
            return result
            
        except Exception as e:
            logger.error(f"통합 스토리 생성 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())  # 스택 트레이스 로깅 추가
            return None
    
    def create_stories_batch(self, keywords: List[str], combine_keywords: bool = False) -> List[Dict[str, Any]]:
        """
        여러 키워드에 대해 일괄적으로 스토리 생성
        
        Args:
            keywords: 스토리 생성에 사용할 키워드 목록
            combine_keywords: True인 경우 모든 키워드를 통합하여 하나의 스토리 생성, 
                             False인 경우 각 키워드별로 스토리 생성
            
        Returns:
            생성된 콘텐츠 목록
        """
        results = []
        
        # 키워드 통합 모드
        if combine_keywords and len(keywords) > 1:
            logger.info(f"{len(keywords)}개 키워드 통합하여 스토리 생성 시작")
            result = self.create_story_from_multiple_keywords(keywords)
            if result:
                results.append(result)
            return results
        
        # 개별 키워드 모드
        total = len(keywords)
        logger.info(f"{total}개 키워드에 대한 일괄 스토리 생성 시작")
        
        for i, keyword in enumerate(keywords, 1):
            logger.info(f"[{i}/{total}] '{keyword}' 처리 중...")
            
            # 스토리 생성
            result = self.create_story_from_keyword(keyword)
            
            if result:
                results.append(result)
                
            # API 요청 사이에 짧은 지연 적용
            if i < total:
                time.sleep(1)
        
        logger.info(f"일괄 처리 완료: {len(results)}/{total} 성공")
        return results
    
    def _save_story(self, story_data: Dict[str, Any]) -> None:
        """
        생성된 스토리 데이터를 파일로 저장
        
        Args:
            story_data: 저장할 스토리 데이터
        """
        try:
            # 날짜 기반 파일명 생성
            today = datetime.now().strftime("%Y%m%d")
            keyword = story_data["keyword"].replace(", ", "_").replace(" ", "_")[:30]  # 파일명 길이 제한
            filename = f"{config.OUTPUT_DIR}/story_{keyword}_{today}.json"
            
            # JSON 형식으로 저장
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"스토리 데이터 저장 완료: {filename}")
            
        except Exception as e:
            logger.error(f"스토리 데이터 저장 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())  # 스택 트레이스 로깅 추가

# 싱글톤 인스턴스 생성
story_generator = StoryGenerator()

def generate_story(keyword: str) -> Optional[Dict[str, Any]]:
    """
    주어진 키워드에 대한 스토리 생성 (편의 함수)
    
    Args:
        keyword: 스토리 생성에 사용할 키워드
        
    Returns:
        생성된 콘텐츠 또는 None
    """
    return story_generator.create_story_from_keyword(keyword)

def generate_stories(keywords: List[str], combine_keywords: bool = False) -> List[Dict[str, Any]]:
    """
    여러 키워드에 대한 스토리 일괄 생성 (편의 함수)
    
    Args:
        keywords: 스토리 생성에 사용할 키워드 목록
        combine_keywords: True인 경우 모든 키워드를 통합하여 하나의 스토리 생성
        
    Returns:
        생성된 콘텐츠 목록
    """
    return story_generator.create_stories_batch(keywords, combine_keywords)