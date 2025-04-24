#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM API 연동 모듈
다양한 LLM API를 활용한 텍스트 생성 기능 제공
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
import sys
import logging
import openai

# 상위 디렉토리 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMProvider:
    """LLM API 통신 클래스"""

    def __init__(self, api_key: str = None, model: str = None):
        """
        LLM 제공자 초기화
        """
        self.api_key = api_key or config.LLM_API_KEY
        self.model = model or config.LLM_MODEL

        # 클라이언트 객체 생성 (최신 OpenAI API 방식)
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"LLM 제공자 초기화: 모델={self.model}")
    
    def generate_text(self, prompt: str, max_tokens: int = None, 
                     temperature: float = None) -> Optional[str]:
        """
        프롬프트를 기반으로 텍스트 생성
        """
        max_tokens = max_tokens or config.LLM_MAX_TOKENS
        temperature = temperature or config.LLM_TEMPERATURE

        try:
            logger.debug(f"텍스트 생성 요청: 프롬프트 길이={len(prompt)}")

            # 모델에 따라 적절한 API 호출
            if "gpt" in self.model.lower():
                return self._generate_with_openai(prompt, max_tokens, temperature)
            elif "gemma" in self.model.lower():
                return self._generate_with_gemma(prompt, max_tokens, temperature)
            else:
                logger.error(f"지원하지 않는 모델: {self.model}")
                return None

        except Exception as e:
            logger.error(f"텍스트 생성 중 오류 발생: {str(e)}")
            return None

    def _generate_with_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """OpenAI API를 사용한 텍스트 생성 (최신 방식)"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "당신은 자극적이고 현실적인 중장년층 대상 '썰' 콘텐츠를 생성하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()

    def _generate_with_gemma(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Gemma API 사용 (미구현)"""
        pass

# 싱글톤 인스턴스 생성
llm_provider = LLMProvider()
