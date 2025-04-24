import os
import json
from datetime import datetime

today = datetime.now().strftime("%Y%m%d")
directory = f"data/{today}"

def format_number(number):
    """숫자를 읽기 쉬운 형식으로 포맷팅"""
    if number >= 100000000:  # 1억 이상
        return f"{number/100000000:.1f}억"
    elif number >= 10000:  # 1만 이상
        return f"{number/10000:.1f}만"
    elif number >= 1000:  # 1천 이상
        return f"{number/1000:.1f}천"
    else:
        return f"{number}"

def check_file_exists(keyword):
    """주어진 키워드에 대한 결과 파일이 이미 존재하는지 확인"""
    filename = f"{directory}/youtube_{keyword}_shorts_{today}.json"
    return filename

def save_results(shorts_data, keyword, min_views, max_days):
    """검색 결과를 날짜 기반 디렉토리에 저장"""
    
    # 디렉토리가 없으면 생성
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # 파일명 생성
    filename = f"{directory}/youtube_{keyword}_shorts_{today}.json"
    
    # 파일 저장
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(shorts_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 결과가 '{filename}' 파일로 저장되었습니다.")
    return filename