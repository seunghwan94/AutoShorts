#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube 페이지 파서 모듈
웹페이지에서 쇼츠 데이터 및 메타데이터 추출
"""

import re
import json
import random
import requests

def extract_shorts_from_page_with_token(url):
    """웹페이지에서 쇼츠 데이터와 연속 토큰 추출"""
    try:
        # 사용자 에이전트 순환 (탐지 방지)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
        ]
        
        # 요청 헤더 설정
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.youtube.com/",
            "sec-ch-ua": "\"Google Chrome\";v=\"124\", \"Not:A-Brand\";v=\"8\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # 연속 토큰이 포함된 URL인지 확인
        if "browse_ajax" in url:
            try:
                # API 요청으로 처리
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    return [], None
                    
                data = response.json()
                return extract_shorts_from_ajax_response(data), extract_continuation_token_from_ajax(data)
            except Exception as e:
                print(f"AJAX 요청 오류: {e}")
                return [], None
        
        # 일반 페이지 요청
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"페이지 요청 실패: {response.status_code}")
            return [], None
        
        # 초기 데이터 추출 (여러 패턴 시도)
        patterns = [
            r'var\s+ytInitialData\s*=\s*({.+?});</script>',
            r'window\["ytInitialData"\]\s*=\s*({.+?});</script>',
            r'ytInitialData\s*=\s*({.+?});</script>'
        ]
        
        data_match = None
        for pattern in patterns:
            matches = re.search(pattern, response.text, re.DOTALL)
            if matches:
                data_match = matches
                break
        
        if not data_match:
            print("페이지에서 데이터를 찾을 수 없습니다.")
            return [], None
        
        try:
            # JSON 파싱
            data = json.loads(data_match.group(1))
            
            # 쇼츠 데이터와 연속 토큰 추출
            shorts_data = extract_shorts_from_data(data)
            continuation_token = extract_continuation_token(data)
            
            return shorts_data, continuation_token
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return [], None
            
    except Exception as e:
        print(f"페이지 처리 중 오류: {str(e)}")
        return [], None

def extract_shorts_from_ajax_response(data):
    """AJAX 응답에서 쇼츠 데이터 추출"""
    shorts_data = []
    
    try:
        # 응답 구조에 따라 처리
        if isinstance(data, list) and len(data) >= 1:
            response_data = data[1].get("response", {})
        else:
            response_data = data.get("response", {})
        
        # onResponseReceivedActions 확인
        actions = response_data.get("onResponseReceivedActions", [])
        for action in actions:
            if "appendContinuationItemsAction" in action:
                items = action["appendContinuationItemsAction"].get("continuationItems", [])
                shorts_data.extend(process_items(items))
        
        return shorts_data
    except Exception as e:
        print(f"AJAX 응답 처리 오류: {e}")
        return []

def extract_continuation_token_from_ajax(data):
    """AJAX 응답에서 연속 토큰 추출"""
    try:
        if isinstance(data, list) and len(data) >= 1:
            response_data = data[1].get("response", {})
        else:
            response_data = data.get("response", {})
        
        actions = response_data.get("onResponseReceivedActions", [])
        for action in actions:
            if "appendContinuationItemsAction" in action:
                items = action["appendContinuationItemsAction"].get("continuationItems", [])
                for item in items:
                    if "continuationItemRenderer" in item:
                        token = item["continuationItemRenderer"].get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                        if token:
                            return token
        return None
    except Exception as e:
        print(f"연속 토큰 추출 오류: {e}")
        return None
        
def extract_shorts_from_data(data):
    """데이터에서 쇼츠 항목 추출"""
    shorts_data = []
    
    try:
        # 여러 가능한 콘텐츠 경로 탐색
        content_paths = [
            # 검색 결과 경로
            data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", []),
            # 홈피드 경로
            data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", []),
            # 채널 페이지 경로
            data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("secondaryContents", {}).get("sectionListRenderer", {}).get("contents", []),
            # 쇼츠 탭 경로
            data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("richGridRenderer", {}).get("contents", [])
        ]
        
        for content_path in content_paths:
            if not content_path:
                continue
            
            # 탭 처리 (twoColumnBrowseResultsRenderer.tabs)
            if isinstance(content_path, list) and content_path and "tabRenderer" in content_path[0]:
                for tab in content_path:
                    if "tabRenderer" in tab:
                        tab_content = tab["tabRenderer"].get("content", {})
                        
                        # 섹션 리스트 처리
                        if "sectionListRenderer" in tab_content:
                            sections = tab_content["sectionListRenderer"].get("contents", [])
                            for section in sections:
                                # 아이템 섹션 렌더러 처리
                                if "itemSectionRenderer" in section:
                                    items = section["itemSectionRenderer"].get("contents", [])
                                    shorts_data.extend(process_items(items))
                        
                        # 리치 그리드 처리
                        elif "richGridRenderer" in tab_content:
                            items = tab_content["richGridRenderer"].get("contents", [])
                            shorts_data.extend(process_items(items))
            
            # 섹션 리스트 처리 (일반 검색 결과)
            elif isinstance(content_path, list):
                for section in content_path:
                    # 아이템 섹션 렌더러 처리
                    if "itemSectionRenderer" in section:
                        items = section["itemSectionRenderer"].get("contents", [])
                        shorts_data.extend(process_items(items))
                    # 리치 그리드 처리
                    elif "richGridRenderer" in section:
                        items = section["richGridRenderer"].get("contents", [])
                        shorts_data.extend(process_items(items))
            
            # 리치 그리드 콘텐츠 직접 처리
            elif isinstance(content_path, list):
                shorts_data.extend(process_items(content_path))
        
        return shorts_data
        
    except Exception as e:
        print(f"데이터 처리 중 오류: {str(e)}")
        return []

def extract_continuation_token(data):
    """데이터에서 연속 토큰 추출"""
    try:
        # 가능한 토큰 경로 확인
        # 1. 검색 결과 내 토큰
        search_contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
        for item in search_contents:
            if "continuationItemRenderer" in item:
                token = item["continuationItemRenderer"].get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                if token:
                    return token
        
        # 2. 탭 내 토큰
        tabs = data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
        for tab in tabs:
            if "tabRenderer" in tab:
                tab_content = tab["tabRenderer"].get("content", {})
                
                # 리치 그리드 내 토큰
                if "richGridRenderer" in tab_content:
                    rich_contents = tab_content["richGridRenderer"].get("contents", [])
                    for item in rich_contents:
                        if "continuationItemRenderer" in item:
                            token = item["continuationItemRenderer"].get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                            if token:
                                return token
                
                # 섹션 리스트 내 토큰
                elif "sectionListRenderer" in tab_content:
                    sections = tab_content["sectionListRenderer"].get("contents", [])
                    for section in sections:
                        if "continuationItemRenderer" in section:
                            token = section["continuationItemRenderer"].get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                            if token:
                                return token
                        
                        # 아이템 섹션 내 토큰
                        elif "itemSectionRenderer" in section:
                            items = section["itemSectionRenderer"].get("contents", [])
                            for item in items:
                                if "continuationItemRenderer" in item:
                                    token = item["continuationItemRenderer"].get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                                    if token:
                                        return token
        
        # 3. 리치 그리드 직접 확인
        grid_contents = data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("richGridRenderer", {}).get("contents", [])
        if grid_contents:
            for item in grid_contents:
                if "continuationItemRenderer" in item:
                    token = item["continuationItemRenderer"].get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                    if token:
                        return token
        
        return None
    except Exception as e:
        print(f"연속 토큰 추출 중 오류: {str(e)}")
        return None
        
def process_items(items):
    """아이템 목록에서 쇼츠 추출"""
    shorts_data = []
    
    for item in items:
        # 비디오 렌더러 처리
        if "videoRenderer" in item:
            video = item["videoRenderer"]
            if detect_if_short(video):
                video_info = extract_video_info(video)
                if video_info:
                    shorts_data.append(video_info)
        
        # 릴 아이템 렌더러 처리 (쇼츠)
        elif "reelItemRenderer" in item:
            reel = item["reelItemRenderer"]
            video_info = extract_video_info(reel, is_reel=True)
            if video_info:
                shorts_data.append(video_info)
        
        # 리치 아이템 렌더러 처리
        elif "richItemRenderer" in item:
            rich_content = item["richItemRenderer"].get("content", {})
            
            # 릴 아이템 렌더러 처리
            if "reelItemRenderer" in rich_content:
                reel = rich_content["reelItemRenderer"]
                video_info = extract_video_info(reel, is_reel=True)
                if video_info:
                    shorts_data.append(video_info)
            
            # 비디오 렌더러 처리
            elif "videoRenderer" in rich_content:
                video = rich_content["videoRenderer"]
                if detect_if_short(video):
                    video_info = extract_video_info(video)
                    if video_info:
                        shorts_data.append(video_info)
        
        # 그리드 비디오 렌더러 처리
        elif "gridVideoRenderer" in item:
            video = item["gridVideoRenderer"]
            if detect_if_short(video):
                video_info = extract_video_info(video)
                if video_info:
                    shorts_data.append(video_info)
    
    return shorts_data

def detect_if_short(video):
    """비디오가 쇼츠인지 감지"""
    # 방법 1: 내비게이션 URL 확인
    if "navigationEndpoint" in video:
        endpoint = video["navigationEndpoint"]
        if "commandMetadata" in endpoint:
            metadata = endpoint["commandMetadata"]
            if "webCommandMetadata" in metadata:
                url = metadata["webCommandMetadata"].get("url", "")
                if "/shorts/" in url:
                    return True
    
    # 방법 2: 길이 확인 (60초 이하)
    length_text = extract_text(video.get("lengthText", {}))
    if length_text:
        if ":" in length_text:
            parts = length_text.split(":")
            if len(parts) == 2 and parts[0] == "0" and int(parts[1]) <= 60:
                return True
    
    # 방법 3: 썸네일 비율 확인
    if "thumbnail" in video and "thumbnails" in video["thumbnail"]:
        thumbnails = video["thumbnail"]["thumbnails"]
        if thumbnails:
            thumb = thumbnails[-1]
            if "width" in thumb and "height" in thumb:
                if thumb.get("height", 0) > thumb.get("width", 0):
                    return True
    
    # 방법 4: 배지 확인
    if "badges" in video:
        for badge in video["badges"]:
            if "metadataBadgeRenderer" in badge:
                badge_label = badge["metadataBadgeRenderer"].get("label", "")
                if "shorts" in badge_label.lower():
                    return True
    
    # 방법 5: 제목에 #shorts 포함 여부
    title = extract_text(video.get("title", {}))
    if "#shorts" in title.lower():
        return True
    
    return False

def extract_video_info(video, is_reel=False):
    """비디오/릴 렌더러에서 기본 정보 추출 (설명 상세 조회 없이)"""
    try:
        video_id = video.get("videoId")
        if not video_id:
            return None
        
        # 제목 (릴과 비디오 렌더러의 구조가 다름)
        title_container = video.get("headline" if is_reel else "title", {})
        title = extract_text(title_container)
        
        # 조회수
        view_count_text = extract_text(video.get("viewCountText", {}))
        views = parse_view_count(view_count_text)
        
        # 게시 시간
        published_time = extract_text(video.get("publishedTimeText", {}))
        
        # 채널 정보
        channel_name = ""
        channel_id = ""
        
        # 릴 렌더러와 비디오 렌더러에서 채널 정보 추출 방식이 다름
        if "ownerText" in video:
            channel_name = extract_text(video["ownerText"])
            
            # 채널 ID 추출
            if "runs" in video["ownerText"]:
                for run in video["ownerText"]["runs"]:
                    if "navigationEndpoint" in run:
                        endpoint = run["navigationEndpoint"]
                        if "browseEndpoint" in endpoint:
                            channel_id = endpoint["browseEndpoint"].get("browseId", "")
                            break
        
        # 썸네일
        thumbnail_url = ""
        if "thumbnail" in video and "thumbnails" in video["thumbnail"]:
            thumbnails = video["thumbnail"]["thumbnails"]
            if thumbnails:
                thumbnail_url = thumbnails[-1].get("url", "")
        
        # 비디오 URL
        video_url = f"https://www.youtube.com/shorts/{video_id}"
        
        # 기본 설명만 추출 (API 호출 없이)
        description = ""
        if "descriptionSnippet" in video:
            description = extract_text(video.get("descriptionSnippet", {}))
        
        if not description and "detailedMetadataSnippets" in video:
            metadata_snippets = video.get("detailedMetadataSnippets", [])
            for snippet in metadata_snippets:
                if "snippetText" in snippet:
                    snippet_text = snippet.get("snippetText", {})
                    snippet_description = extract_text(snippet_text)
                    if snippet_description:
                        description = snippet_description
                        break

        return {
            "video_id": video_id,
            "title": title,
            "view_count_text": view_count_text,
            "views": views,
            "published_time": published_time,
            "channel_name": channel_name,
            "channel_id": channel_id,
            "thumbnail_url": thumbnail_url,
            "description": description,
            "video_url": video_url
        }
        
    except Exception as e:
        print(f"비디오 정보 추출 중 오류: {str(e)}")
        return None

def extract_text(text_container):
    """텍스트 컨테이너에서 텍스트 추출"""
    if not text_container:
        return ""
    
    if "simpleText" in text_container:
        return text_container["simpleText"]
    elif "runs" in text_container:
        return "".join([run.get("text", "") for run in text_container["runs"]])
    
    return ""

def parse_view_count(view_count_text):
    """조회수 텍스트에서 숫자 추출"""
    if not view_count_text:
        return 0
    
    # 한국어 조회수 패턴 처리 ("조회수 1.5만회", "조회수 1000회" 등)
    match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*([천만억])?회', view_count_text)
    if match:
        # 콤마(,) 제거 후 숫자 변환
        number_str = match.group(1).replace(',', '')
        number = float(number_str)
        unit = match.group(2) if match.group(2) else ""
        
        multiplier = {
            "": 1,
            "천": 1000,
            "만": 10000,
            "억": 100000000
        }.get(unit, 1)
        
        return int(number * multiplier)
    
    # 영어 패턴 처리 ("1.5M views", "1K views" 등)
    en_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*([KMB])', view_count_text, re.IGNORECASE)
    if en_match:
        number_str = en_match.group(1).replace(',', '')
        number = float(number_str)
        unit = en_match.group(2).upper()
        
        multiplier = {
            "K": 1000,
            "M": 1000000,
            "B": 1000000000
        }.get(unit, 1)
        
        return int(number * multiplier)
    
    # 단순 숫자 추출
    numbers = re.findall(r'\d+', view_count_text)
    if numbers:
        try:
            # 콤마 제거 후 모든 숫자 연결
            number_str = "".join(numbers).replace(',', '')
            return int(number_str)
        except:
            pass
    
    return 0

