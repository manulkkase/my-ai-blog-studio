import os

def fetch_topic() -> str:
    """
    topics.txt 파일에서 다음 포스팅 주제를 가져오고, 처리된 주제는 파일에서 제거합니다.
    가장 먼저 사용되어야 할 도구입니다.
    """
    file_path = 'topics.txt'
    try:
        with open(file_path, 'r+', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                return "처리할 주제가 없습니다."

            topic = lines[0].strip()

            f.seek(0)
            f.writelines(lines[1:])
            f.truncate()

            return topic
    except FileNotFoundError:
        return f"오류: {file_path} 파일을 찾을 수 없습니다."
    except Exception as e:
        return f"오류: 주제를 가져오는 중 예상치 못한 오류가 발생했습니다 - {e}"

if __name__ == '__main__':
    # For standalone testing
    print("Fetching topic...")
    # Create a dummy topics.txt for testing if it doesn't exist
    if not os.path.exists('topics.txt'):
        with open('topics.txt', 'w', encoding='utf-8') as f:
            f.write("테스트 주제 1\n")
            f.write("테스트 주제 2\n")
    
    topic = fetch_topic()
    print(f"가져온 주제: {topic}")
    print("topics.txt 내용 확인:")
    with open('topics.txt', 'r', encoding='utf-8') as f:
        print(f.read())
