import os
import sys
import re
from typing import Tuple, List

# --- Tool Imports ---
# Ensure the tools directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from topic_fetcher import fetch_topic
from article_generator import generate_article
from category_assigner import assign_category
from image_creator import create_image
from github_publisher import publish_to_github

# --- Keyword Parsing ---
def parse_keywords(topic_line: str) -> Tuple[str, List[str]]:
    """Helper function to parse keywords from a string."""
    primary_match = re.search(r"Primary:\s*(.*?)(;|$)", topic_line)
    secondary_match = re.search(r"Secondary:\s*(.*)", topic_line)
    primary_keyword = primary_match.group(1).strip() if primary_match else ""
    if secondary_match and secondary_match.group(1):
        secondary_keywords: List[str] = [kw.strip() for kw in secondary_match.group(1).split(',')]
    else:
        secondary_keywords: List[str] = []
    return primary_keyword, secondary_keywords

# --- Main Execution Logic ---
def main():
    """Main function to run the entire blog creation pipeline."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo_name = os.getenv("GITHUB_REPO_NAME")

    if not all([openai_api_key, github_token, github_repo_name]):
        print("Error: Required environment variables are not set.")
        sys.exit(1)

    topic_line = fetch_topic()
    if not topic_line or "처리할 주제가 없습니다" in topic_line:
        print("No topics to process. Exiting.")
        return

    print(f"--- Starting Blog Post Generation for topic ---")
    print(f"Topic: {topic_line}")
    print("----------------------------------------------------")

    primary_keyword, secondary_keywords = parse_keywords(topic_line)
    if not primary_keyword:
        print("Error: Could not parse the primary keyword from the topic line.")
        sys.exit(1)

    # 1. Generate Article
    print(f"Generating article for: {primary_keyword}")
    article_content = generate_article(primary_keyword, secondary_keywords, api_key=openai_api_key)
    if "Error:" in article_content:
        print(f"Failed to generate article: {article_content}")
        sys.exit(1)

    # 2. Assign Category
    print(f"Assigning category for: {primary_keyword}")
    category = assign_category(primary_keyword, api_key=openai_api_key)
    if "Error:" in category:
        print(f"Failed to assign category: {category}")
        sys.exit(1)

    # 3. Create Image
    print(f"Creating image for: {primary_keyword}")
    body_content = "\n".join(article_content.split('\n')[2:])
    image_path = create_image(body_content, primary_keyword)
    if "Error:" in image_path:
        print(f"Failed to create image: {image_path}")
        # sys.exit(1)

    # 4. Publish to GitHub
    print(f"Publishing post for: {primary_keyword}")
    title = article_content.split('\n')[0].strip()
    result = publish_to_github(
        title=title,
        full_article_content=article_content,
        category=category,
        image_local_path=image_path,
        github_token=github_token,
        repo_name=github_repo_name
    )
    
    print("--- Pipeline Finished ---")
    print(f"Final Output: {result}")
    print("-------------------------")

if __name__ == "__main__":
    main()
