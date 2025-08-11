import os
from openai import OpenAI, APIError

def assign_category(topic: str, api_key: str) -> str:
    """
    주어진 주제(topic)를 분석하여, 정의된 6개의 카테고리 중 가장 적합한 카테고리 하나를 결정합니다.
    """
    if not topic or "오류:" in topic:
        return "분류할 유효한 주제가 없습니다."

    categories = [
        "K-Culture & Palaces",
        "Street Food & Night Markets",
        "Mountains & Rice Terraces",
        "Beaches, Bays & Islands",
        "City Vibes & Night-life",
        "Budget Hacks & Transport"
    ]

    try:
        client = OpenAI(api_key=api_key)
        system_prompt = """
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
        if assigned_category in categories:
            return assigned_category
        else:
            for cat in categories:
                if cat.split(' ')[0].lower() in assigned_category.lower():
                    return cat
            return "Uncategorized"
    except APIError as e:
        return f"오류: 카테고리 분류 중 OpenAI API 오류 발생 - {e}"
    except Exception as e:
        return f"오류: 카테고리 분류 중 예상치 못한 오류 발생 - {e}"