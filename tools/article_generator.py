import os
from openai import OpenAI, APIError
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

def generate_article(topic: str) -> str:
    """
    주어진 주제에 기반하여 고품질의 블로그 글을 생성합니다.
    topic_fetcher_tool이 성공적으로 주제를 가져온 후에 사용되어야 합니다.
    """
    if not topic or "처리할 주제가 없습니다" in topic or "오류:" in topic:
        return "글을 생성하기 위한 유효한 주제가 없습니다. 이전 단계를 확인해주세요."

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        system_prompt = """
        당신은 15년차 베테랑 여행 블로거 '노마드 작가'입니다.
        당신의 글은 깊이 있는 정보와 생생한 경험담이 잘 어우러져 독자들에게 큰 신뢰를 줍니다.
        항상 다음 구조에 맞춰 글을 작성해주세요.

        # {주제}

        ## 서론 (독자의 흥미를 유발하는 도입)
        ...

        ## 본론 (소제목을 2~3개 사용하여 구체적인 정보 제공)
        ### 소제목 1
        ...
        ### 소제목 2
        ...

        ## 결론 (핵심 내용을 요약하고, 다음 여행을 독려하는 마무리)
        ...

        - 마크다운 형식을 사용해주세요.
        - 친근하지만 전문가적인 어조를 유지해주세요.
        - 각 섹션은 최소 2~3문단으로 구성해주세요.
        """

        user_prompt = f"'{topic}'을 주제로 블로그 포스팅을 작성해주세요."

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
        )

        article = response.choices[0].message.content
        return article.strip()

    except APIError as e:
        return f"오류: OpenAI API 호출 중 에러가 발생했습니다 - {e}"
    except Exception as e:
        return f"오류: 글을 생성하는 중 예상치 못한 오류가 발생했습니다 - {e}"

if __name__ == '__main__':
    # For standalone testing
    test_topic = "치앙마이 한달살기 비용"
    print(f"Generating article for topic: {test_topic}")
    article_content = generate_article(test_topic)
    print("--- Generated Article ---")
    print(article_content)
    print("-------------------------")
