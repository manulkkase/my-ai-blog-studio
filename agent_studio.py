import os
import sys
import re
from typing import Tuple, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool

# --- Tool Imports ---
# Ensure the tools directory is in the Python path
sys.path.append(os.path.dirname(__file__))
from tools.topic_fetcher import fetch_topic
from tools.article_generator import generate_article
from tools.category_assigner import assign_category
from tools.image_creator import create_image
from tools.github_publisher import publish_to_github

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

# --- Tool Definition ---
@tool
def full_blog_creation_pipeline(topic_line: str, openai_api_key: str, github_token: str, github_repo_name: str) -> str:
    """
    Handles the entire blog post creation process from a single topic line.
    Requires API keys and the target repository name to be passed as arguments.
    """
    primary_keyword, secondary_keywords = parse_keywords(topic_line)
    if not primary_keyword:
        return "Error: Could not parse the primary keyword."

    print(f"Generating article for: {primary_keyword}")
    article_content = generate_article(primary_keyword, secondary_keywords, api_key=openai_api_key)
    if "Error:" in article_content:
        return article_content

    print(f"Assigning category for: {primary_keyword}")
    category = assign_category(primary_keyword, api_key=openai_api_key)
    if "Error:" in category:
        return category

    print(f"Creating image for: {primary_keyword}")
    body_content = "\n".join(article_content.split('\n')[2:])
    image_path = create_image(body_content, primary_keyword, api_key=openai_api_key)
    if "Error:" in image_path:
        return image_path

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
    return result

# --- Agent Setup ---
def main():
    """Main function to initialize and run the Blog Studio Agent."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo_name = os.getenv("GITHUB_REPO_NAME")

    if not all([openai_api_key, github_token, github_repo_name]):
        print("Error: Required environment variables are not set.")
        sys.exit(1)

    tools = [full_blog_creation_pipeline]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a supervisor AI. Your only job is to call the `full_blog_creation_pipeline` tool with the provided `topic_line` and all the required API keys and repository information."),
        ("user", "{topic_line}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, api_key=openai_api_key)
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    topic_line = fetch_topic()
    if not topic_line or "처리할 주제가 없습니다" in topic_line:
        print("No topics to process. Exiting.")
        return

    print(f"--- Blog Studio Agent starting with topic ---")
    print(f"Topic: {topic_line}")
    print("----------------------------------------------------")

    response = agent_executor.invoke({
        "topic_line": topic_line,
        "openai_api_key": openai_api_key,
        "github_token": github_token,
        "github_repo_name": github_repo_name,
    })

    print("--- Agent execution finished ---")
    print(f"Final Output: {response['output']}")
    print("--------------------------------")

if __name__ == "__main__":
    main()