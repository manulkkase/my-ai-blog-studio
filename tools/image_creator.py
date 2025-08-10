import os
import re
import requests
from datetime import datetime
from openai import OpenAI, APIError
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

def create_image(article_content: str, topic: str) -> str:
    """
    생성된 글의 내용과 주제를 바탕으로 DALL-E 3를 사용하여 어울리는 이미지를 생성하고,
    'static/images/' 경로에 저장합니다.
    article_generator_tool이 성공적으로 글을 생성한 후에 사용되어야 합니다.
    """
    if "오류:" in article_content or not article_content:
        return "이미지를 생성하기 위한 유효한 글 내용이 없습니다. 이전 단계를 확인해주세요."

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # 이미지 생성 프롬프트를 위한 요약 생성 (LLM 호출)
        summary_prompt = f"""
        너는 내셔널 지오그래픽 소속의 베테랑 여행 사진작가다. 주어진 블로그 글의 핵심을 꿰뚫는 단 한 장의 대표 사진을 만들어야 한다.

        **[미션]**
        다음 블로그 글을 분석하여, 마치 독자가 그 순간을 직접 엿보는 듯한 느낌을 주는 '결정적 순간(The Decisive Moment)'을 포착해줘.

        **[촬영 가이드라인]**
        1.  **스타일:** 꾸며낸 스튜디오 사진이 아닌, 현장의 날것(RAW) 느낌을 살린 포토 저널리즘 스타일.
        2.  **카메라/렌즈:** 라이카(Leica) M11 카메라와 35mm 단렌즈로 촬영한 듯한 질감.
        3.  **조명:** 인공조명은 절대 사용 금지. 오직 현장의 자연광(natural light)만을 활용하며, 특히 해 질 녘의 부드러운 빛(golden hour)을 선호.
        4.  **구성:** 피사체는 완벽하게 중앙에 놓기보다, '3분할 법칙(Rule of Thirds)'에 따라 자연스럽게 배치하여 깊이와 균형감을 더할 것.
        5.  **결과물:** 최종 프롬프트는 반드시 영어로, 쉼표로 구분된 핵심 묘사들의 나열 형태여야 한다.

        **[분석할 블로그 내용]**
        ---
        {article_content[:1000]}
        ---
        """
        
        summary_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=100,
        )
        image_prompt = summary_response.choices[0].message.content.strip()
        print(f"Generated Image Prompt: {image_prompt}")


        # DALL-E 3 호출
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="url"
        )
        
        image_url = image_response.data[0].url

        # 주제를 기반으로 고유한 파일명 생성 (영문, 소문자, 하이픈)
        file_name_base = re.sub(r'[^a-z0-9\s-]', '', topic.lower()).strip()
        file_name_base = re.sub(r'\s+', '-', file_name_base)
        if not file_name_base:
            file_name_base = "blog-post"
        
        # 타임스탬프를 추가하여 파일 이름의 고유성 보장
        timestamp = datetime.now().strftime("%H%M%S")
        file_name = f"{file_name_base}-{timestamp}.jpg"

        # 임시 로컬 경로에 이미지 저장
        image_path = file_name

        # 이미지 다운로드 및 저장
        img_data = requests.get(image_url).content
        with open(image_path, 'wb') as handler:
            handler.write(img_data)

        return image_path

    except APIError as e:
        return f"오류: DALL-E API 호출 중 에러가 발생했습니다 - {e}"
    except requests.exceptions.RequestException as e:
        return f"오류: 이미지 다운로드 중 에러가 발생했습니다 - {e}"
    except Exception as e:
        return f"오류: 이미지를 생성/저장하는 중 예상치 못한 오류가 발생했습니다 - {e}"

if __name__ == '__main__':
    # For standalone testing
    test_topic = "교토의 숨겨진 명소"
    test_article = """
    # 교토의 숨겨진 명소

    ## 서론
    교토는 천년 고도의 역사를 간직한 도시로, 수많은 관광객들이 찾는 곳입니다. 하지만 화려한 금각사나 북적이는 기요미즈데라 외에도, 교토의 진짜 매력을 느낄 수 있는 숨겨진 장소들이 많이 있습니다. 이번 포스팅에서는 현지인들만 아는 교토의 비밀스러운 명소들을 소개해드리겠습니다.

    ## 본론
    ### 1. 철학의 길 끝자락, 호넨인
    철학의 길은 유명하지만, 대부분의 관광객들은 길의 시작점에서 발길을 돌립니다. 하지만 길의 끝까지 걸어가면 고즈넉한 사찰, 호넨인을 만날 수 있습니다. 이곳은 화려함 대신 소박함과 정적인 아름다움이 돋보이는 곳으로, 특히 이끼 낀 산문은 시간의 흐름을 느끼게 해줍니다.

    ### 2. 대나무 숲의 또 다른 얼굴, 아다시노 넨부츠지
    아라시야마의 치쿠린은 항상 인산인해를 이룹니다. 조금 더 여유롭게 대나무 숲을 즐기고 싶다면 아다시노 넨부츠지를 추천합니다. 이곳은 수천 개의 석불과 석탑이 대나무 숲과 어우러져 독특하고 신비로운 분위기를 자아냅니다.

    ## 결론
    교토 여행을 계획하고 있다면, 하루쯤은 유명 관광지를 벗어나 자신만의 '숨겨진 명소'를 찾아보는 것은 어떨까요? 오늘 소개해드린 곳들에서 여러분은 분명 교토의 새로운 얼굴을 발견하게 될 것입니다.
    """
    print(f"Creating image for topic: {test_topic}")
    image_path_result = create_image(test_article, test_topic)
    print(f"--- Image Creator Result ---")
    print(f"Image saved at: {image_path_result}")
    print("--------------------------")
    # Verify file exists
    if "오류:" not in image_path_result and os.path.exists(image_path_result):
        print("Verification: Image file created successfully.")
    else:
        print("Verification: Image file creation failed.")

