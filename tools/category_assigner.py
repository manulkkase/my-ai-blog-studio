import os
from openai import OpenAI, APIError

def assign_category(topic: str) -> str:
    """
    주어진 주제(topic)를 분석하여, 정의된 6개의 카테고리 중 가장 적합한 카테고리 하나를 결정합니다.
    article_generator_tool이 글을 생성한 후에 사용되어야 합니다.
    """
    if not topic or "오류:" in topic:
        return "분류할 유효한 주제가 없습니다."

    # 블로그의 6개 카테고리 목록
    categories = [
        "K-Culture & Palaces",
        "Street Food & Night Markets",
        "Mountains & Rice Terraces",
        "Beaches, Bays & Islands",
        "City Vibes & Night-life",
        "Budget Hacks & Transport"
    ]

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        system_prompt = f"""
        당신은 블로그 콘텐츠를 정확하게 분류하는 카테고리 전문가입니다.
        사용자의 블로그 주제를 보고, 아래에 정의된 6개의 카테고리 중 가장 적합한 카테고리 *하나만* 골라야 합니다.
        다른 설명 없이, 오직 카테고리 이름만 정확하게 반환해야 합니다.

        [카테고리 목록]
        - K-Culture & Palaces
        - Street Food & Night Markets
        - Mountains & Rice Terraces
        - Beaches, Bays & Islands
        - City Vibes & Night-life
        - Budget Hacks & Transport
        """

        user_prompt = f"블로그 주제: '{topic}'"

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=50,
        )

        assigned_category = response.choices[0].message.content.strip()

        # LLM이 목록에 있는 카테고리명과 정확히 일치하는 답변을 했는지 확인
        if assigned_category in categories:
            return assigned_category
        else:
            # 만약의 경우를 대비한 폴백(Fallback) - 가장 관련성 높아보이는 카테고리 찾기
            for cat in categories:
                if cat.split(' ')[0].lower() in assigned_category.lower():
                    return cat
            return "Uncategorized" # 최악의 경우

    except APIError as e:
        return f"오류: 카테고리 분류 중 OpenAI API 오류 발생 - {e}"
    except Exception as e:
        return f"오류: 카테고리 분류 중 예상치 못한 오류 발생 - {e}"

if __name__ == '__main__':
    # For standalone testing
    test_topic_1 = "서울 경복궁 야간개장 관람 후기"
    test_topic_2 = "부산 해운대 근처 가성비 숙소 추천"
    test_topic_3 = "제주도 한라산 등반 코스 완벽 가이드"

    print(f"주제: '{test_topic_1}'")
    print(f"결정된 카테고리: {assign_category(test_topic_1)}")
    print("-" * 20)
    print(f"주제: '{test_topic_2}'")
    print(f"결정된 카테고리: {assign_category(test_topic_2)}")
    print("-" * 20)
    print(f"주제: '{test_topic_3}'")
    print(f"결정된 카테고리: {assign_category(test_topic_3)}")
