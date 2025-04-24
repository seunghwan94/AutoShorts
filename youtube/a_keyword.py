import json
import os

from youtube.b_crowling import get_shorts_by_keyword
from common.utils import format_number, save_results, check_file_exists


def setting():
    """메인 실행 함수: 사용자 입력을 받고 검색 실행"""
    try:
        # 사용자 입력 받기
        # keyword = input("검색할 키워드를 입력하세요: ").strip()
        keyword = "동물"
        min_views_input = 100000
        days_input = 5
        results_input = 5

        if not keyword:
            print("키워드를 입력해야 합니다.")
            return None
        
        # # 이미 해당 키워드에 대한 결과 파일이 존재하는지 확인
        # filename = check_file_exists(f"youtube_{keyword}_shorts")

        # if os.path.exists(filename):
        #     print(f"\n✅ '{keyword}' 키워드에 대한 결과가 이미 존재합니다.")
        #     return filename # 프로그램 종료 신호
           
        # 필터 설정
        try:
            # min_views_input = input("최소 조회수를 입력하세요 (기본값: 100000): ").strip()
            
            min_views = int(min_views_input) if min_views_input else 100000
        except ValueError:
            print("유효하지 않은 조회수입니다. 기본값 100,000을 사용합니다.")
            min_views = 100000
        
        try:
            # days_input = input("최근 며칠 이내의 쇼츠를 검색할까요? (기본값: 3): ").strip()
            
            max_days = int(days_input) if days_input else 3
        except ValueError:
            print("유효하지 않은 일수입니다. 기본값 3일을 사용합니다.")
            max_days = 3
        
        try:
            # results_input = input("가져올 최대 결과 수는? (기본값: 50): ").strip()
            max_results = int(results_input) if results_input else 50
        except ValueError:
            print("유효하지 않은 결과 수입니다. 기본값 50개를 사용합니다.")
            max_results = 50
        
        print(f"\n검색 설정:")
        print(f"- 키워드: '{keyword}'")
        print(f"- 최소 조회수: {min_views:,}회 이상")
        print(f"- 최근 기간: {max_days}일 이내")
        print(f"- 최대 결과 수: {max_results}개")
        
        # 쇼츠 데이터 가져오기 - 이미 필터링된 결과만 반환됨
        shorts_data = get_shorts_by_keyword(
            keyword=keyword,
            min_views=min_views,
            max_days=max_days,
            max_results=max_results
        )
        
        if not shorts_data:
            print(f"필터 조건을 만족하는 '{keyword}' 관련 쇼츠를 찾을 수 없습니다.")
            return None
        
        # 결과 출력
        print(f"\n🔥 인기 '{keyword}' 쇼츠 TOP {len(shorts_data)}")
        print(f"(모든 결과는 최근 {max_days}일 이내 + 조회수 {min_views:,}회 이상 조건을 충족함)")
        print("-" * 60)
        
        for i, short in enumerate(shorts_data, 1):
            views = short.get("views", 0)
            formatted_views = format_number(views)
            
            print(f"{i}. {short.get('title', '제목 없음')}")
            print(f"   조회수: {short.get('view_count_text', '정보 없음')} ({formatted_views})")
            print(f"   게시일: {short.get('published_time', '정보 없음')}")
            print(f"   채널: {short.get('channel_name', '정보 없음')}")
            print(f"   URL: {short.get('video_url', '')}")
            print("-" * 60)
        
        # 메타데이터를 포함한 데이터 구성
        meta_data = {
            "shorts": shorts_data,
            "metadata": {
                "keyword": keyword,
                "min_views": min_views,
                "max_days": max_days,
                "total_items": len(shorts_data)
            }
        }
        
        # 결과 저장
        filename = save_results(f"youtube_{keyword}_shorts", meta_data)
        return filename
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 중단되었습니다.")
        return None
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()  # 상세 오류 추적
        return None