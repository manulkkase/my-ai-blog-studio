import os
import re
from datetime import datetime
from github import Github, GithubException
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

def publish_to_github(title: str, markdown_body: str, image_local_path: str, category: str) -> str:
    """
    최종 글과 이미지를 GitHub 리포지토리의 적절한 위치에 업로드하여 Netlify 배포를 트리거합니다.
    모든 콘텐츠 생성이 완료된 후 마지막에 사용되어야 합니다.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO_NAME") # 예: "your-username/your-blog-repo"

    if not all([github_token, repo_name]):
        return "오류: GITHUB_TOKEN 또는 GITHUB_REPO_NAME 환경변수가 설정되지 않았습니다."
    if "오류:" in markdown_body or not os.path.exists(image_local_path):
        return "오류: GitHub에 발행할 유효한 콘텐츠(글, 이미지)가 없습니다. 이전 단계를 확인해주세요."

    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        # 1. 이미지 업로드
        image_filename = os.path.basename(image_local_path)
        image_repo_path = f"static/images/{image_filename}"

        with open(image_local_path, 'rb') as f:
            image_content = f.read()

        # 동일한 파일이 있는지 확인
        try:
            repo.get_contents(image_repo_path)
            print(f"Image '{image_repo_path}' already exists. Skipping upload.")
            image_url_in_repo = f"/{image_repo_path}"
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path=image_repo_path,
                    message=f"feat: Add image {image_filename}",
                    content=image_content,
                )
                print(f"Image '{image_repo_path}' uploaded to GitHub.")
                image_url_in_repo = f"/{image_repo_path}"
            else:
                raise e

        # 2. 마크다운 파일 생성 및 업로드
        # Frontmatter 생성
        now = datetime.now()
        date_for_frontmatter = now.strftime("%Y-%m-%d")
        frontmatter = f"""---
title: "{title}"
date: {date_for_frontmatter}
image: "{image_url_in_repo}"
category: "{category}"
---"""
        full_markdown_content = frontmatter + "\n" + markdown_body

        # 마크다운 파일명 생성 (고유성 보장)
        time_for_filename = now.strftime("%Y-%m-%d-%H%M%S")
        post_filename_base = re.sub(r'[^a-z0-9\s-]', '', title.lower()).strip()
        post_filename_base = re.sub(r'\s+', '-', post_filename_base)
        if not post_filename_base:
            post_filename_base = "new-blog-post"
        post_filename = f"{time_for_filename}-{post_filename_base}.md"
        
        post_repo_path = f"_posts/{post_filename}"

        # 동일한 파일이 있는지 확인
        try:
            repo.get_contents(post_repo_path)
            return f"오류: 파일 '{post_repo_path}'가 GitHub에 이미 존재합니다. 중복 발행을 방지하기 위해 작업을 중단합니다."
        except GithubException as e:
            if e.status == 404:
                # 파일이 없으면 생성
                commit_result = repo.create_file(
                    path=post_repo_path,
                    message=f"feat: Add post '{title}'",
                    content=full_markdown_content.encode('utf-8'),
                )
                created_file = commit_result['content']
                return f"성공: 포스트가 성공적으로 발행되었습니다. URL: {created_file.html_url}"
            else:
                raise e

    except GithubException as e:
        return f"오류: GitHub API 작업 중 에러가 발생했습니다 (Status: {e.status}) - {e.data}"
    except Exception as e:
        return f"오류: GitHub에 발행하는 중 예상치 못한 오류가 발생했습니다 - {e}"

if __name__ == '__main__':
    # For standalone testing
    # ** Prerequisites for testing **
    # 1. Create a .env file with:
    #    GITHUB_TOKEN="your_personal_access_token"
    #    GITHUB_REPO_NAME="your_github_username/your_repo_name"
    # 2. Create a dummy image file 'static/images/test-image.jpg'
    
    print("--- GitHub Publisher Standalone Test ---")
    
    # Dummy data
    test_title = "Standalone Test Post"
    test_body = "This is the body of a test post created locally."
    dummy_image_dir = "static/images"
    dummy_image_path = os.path.join(dummy_image_dir, "test-image.jpg")

    # Ensure dummy image exists for testing
    if not os.path.exists(dummy_image_path):
        os.makedirs(dummy_image_dir, exist_ok=True)
        with open(dummy_image_path, "w") as f:
            f.write("this is a dummy image")
        print(f"Created dummy image at: {dummy_image_path}")

    if not os.getenv("GITHUB_TOKEN") or not os.getenv("GITHUB_REPO_NAME"):
        print("\n[SKIP] GITHUB_TOKEN or GITHUB_REPO_NAME not found in .env file.")
        print("Please create a .env file and set these variables to run the test.")
    else:
        print(f"Attempting to publish to repo: {os.getenv('GITHUB_REPO_NAME')}")
        result = publish_to_github(test_title, test_body, dummy_image_path)
        print("\n--- Publisher Result ---")
        print(result)
        print("------------------------")

