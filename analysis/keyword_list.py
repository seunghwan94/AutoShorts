import json

def get_rank(file_path, top_n=3):
    """
    키워드 순위 탑 3
    """
    try:
        # 분석 결과 파일 로드
        with open(file_path, 'r', encoding='utf-8') as f:
            keyword_data = json.load(f)
            
        # 상위 3개 통합 키워드 추출
        top_combined = keyword_data.get("top_combined", {})
        top_3_keywords = list(top_combined.keys())[:3]
        
        return top_3_keywords
    except Exception as e:
        print(f"키워드 추출 중 오류 발생: {e}")     
        return None   