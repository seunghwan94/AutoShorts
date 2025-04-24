from youtube.a_keyword import setting
from story.generator import generate_stories
from analysis.keyword_frequency import analyze_keyword_frequency
from analysis.keyword_list import get_rank

if __name__ == "__main__":
    # # 키워드 추출
    # file_path_crowling = setting()

    # # 키워드 빈도수 분석
    # file_path_keyword = analyze_keyword_frequency(file_path_crowling, excluded_words=["shorts"])
    # target_keyword = get_rank(file_path_keyword)

    # 스토리 생성
    generate_stories(["동물","집안"], combine_keywords=True)

