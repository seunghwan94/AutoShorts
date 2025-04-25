from youtube.a_keyword import setting
from story.generator import generate_stories
from analysis.keyword_frequency import analyze_keyword_frequency
from analysis.keyword_list import get_rank
from tts.integration import process_story_file

if __name__ == "__main__":
    # 키워드 추출
    file_path_crowling = setting()

    # 키워드 빈도수 분석
    file_path_keyword = analyze_keyword_frequency(file_path_crowling, excluded_words=["shorts"])
    
    # 빈도수 상위 3개 추출
    target_keyword = get_rank(file_path_keyword, top_n=3)
    
    # 스토리 생성
    file_path_story = generate_stories(target_keyword, combine_keywords=True)

    # TTS 생성 (배경 음악 포함)
    result = process_story_file(file_path_story, speed=1.7, bg_music_path="assets/music/bg.mp3")