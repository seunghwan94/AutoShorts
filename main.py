from youtube.a_keyword import setting
from story.generator import generate_stories

if __name__ == "__main__":
    # setting()
    generate_stories(["동물","집안"], combine_keywords=True)