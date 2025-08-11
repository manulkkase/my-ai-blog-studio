import os
import re
import requests
from datetime import datetime
from openai import OpenAI, APIError

def create_image(article_content: str, topic: str, api_key: str) -> str:
    """
    생성된 글의 내용과 주제를 바탕으로 DALL-E 3를 사용하여 어울리는 이미지를 생성하고,
    'static/images/' 경로에 저장합니다.
    """
    if "오류:" in article_content or not article_content:
        return "이미지를 생성하기 위한 유효한 글 내용이 없습니다. 이전 단계를 확인해주세요."

    try:
        client = OpenAI(api_key=api_key)
        summary_prompt = f"""
You are a world-class travel photographer and creative director. Your mission is to create a single, stunning cover image for a blog post by generating the perfect DALL-E prompt.

You must strictly follow all guidelines below.

---
**[Master Photography Guidelines: The Core Rules]**

1.  **Camera & Lens:** The final image must look like it was shot on a **Sony Alpha 1 with a 35mm f/1.4 prime lens**. This is non-negotiable.
2.  **Style:** The artistic style is a blend of **Hyperrealistic Detail and Documentary Photography**. It must feel authentic, raw, and incredibly detailed—not like a staged AI image.
3.  **Lighting:** Use **only natural light**. You must prioritize the soft, warm, golden hour light (early morning or late afternoon).
4.  **Composition:** Strictly apply the **Rule of Thirds**. The main subject must be off-center.
5.  **Final Prompt Format:** The output MUST be a single line of comma-separated English keywords and phrases. Do not add any explanation.

---
**[Deep Knowledge Base: Southeast Asian Floating Markets]**

To achieve world-class quality, you must infuse your prompt with the deep knowledge from this section. This is your art direction guide.

* **Core Essence:** Capture vibrant chaos, energy, cultural immersion, and the intimate connection between people and the river.
* **Key Visuals:** Colorful boats overflowing with tropical fruits (mangoes, dragon fruits, rambutans), bustling vendors and shoppers, shimmering reflections on the water, stilt houses, and lush vegetation.
* **Emotional Tone:** The image must evoke excitement, discovery, and the warmth of local hospitality.
* **Texture & Detail:** Emphasize hyper-realistic textures of woven baskets, wood carvings, fresh produce, and rich fabrics.
* **Color Palette:** Use a vibrant, saturated palette (rich reds, oranges, yellows, greens) with cinematic LUTs that emphasize tropical warmth without being unnatural.

---
**[Your Mission]**

1.  **Analyze the Core Essence:** Read the provided [Blog Content to Analyze] below.
2.  **Synthesize & Create:** Combine the essence of the blog post with your [Deep Knowledge Base] on floating markets.
3.  **Generate the Prompt:** Create the final DALL-E prompt, ensuring it strictly adheres to all five [Master Photography Guidelines].

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

        image_response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="url"
        )
        image_url = image_response.data[0].url

        file_name_base = re.sub(r'[^a-z0-9\s-]', '', topic.lower()).strip()
        file_name_base = re.sub(r'\s+', '-', file_name_base)
        if not file_name_base:
            file_name_base = "blog-post"
        
        timestamp = datetime.now().strftime("%H%M%S")
        file_name = f"{file_name_base}-{timestamp}.jpg"
        image_path = file_name

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