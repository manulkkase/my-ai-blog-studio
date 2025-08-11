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
        You are a world-class travel photographer creating a single, stunning cover image for a blog post.
        You must adhere strictly to the following guidelines to generate a DALL-E prompt (in English) based on the provided blog content.

        **[Master Photography Guidelines]**

        1.  **Camera & Lens:** The image must look like it was shot on a **Sony Alpha 1** with a **35mm f/1.4 prime lens**.
        2.  **Style:** The artistic style must be a blend of **Hyperrealistic Detail** and **Documentary Photography**. It should feel authentic, raw, and incredibly detailed, not like a staged or overly-edited AI image.
        3.  **Lighting:** Use only **natural light**. Prioritize the soft, warm light of the **golden hour** (early morning or late afternoon).
        4.  **Composition:** Apply the **Rule of Thirds**. The main subject should be placed off-center to create balance and depth.
        5.  **Final Prompt Format:** The output MUST be a comma-separated list of descriptive keywords and phrases in English.

        **[Your Mission]**

        Analyze the core essence of the blog post below and generate the DALL-E prompt that will create the perfect cover image, following all the master guidelines above.

        **[Blog Content to Analyze]**
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

