import os
import sys
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools import tool

# --- Tool Imports ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from topic_fetcher import fetch_topic
from article_generator import generate_article
from category_assigner import assign_category
from image_creator import create_image
from github_publisher import publish_to_github

# --- Keyword Parsing ---
def parse_keywords(topic_line: str) -> (str, list[str]):
    """Helper function to parse keywords from a string."""
    primary_match = re.search(r"Primary:\s*(.*?)(;|$)", topic_line)
    secondary_match = re.search(r"Secondary:\s*(.*)", topic_line)
    primary_keyword = primary_match.group(1).strip() if primary_match else ""
    if secondary_match and secondary_match.group(1):
        secondary_keywords = [kw.strip() for kw in secondary_match.group(1).split(',')]
    else:
        secondary_keywords = []
    return primary_keyword, secondary_keywords

# --- Tool Definitions ---

@tool
def full_blog_creation_pipeline_tool(topic_line: str, openai_api_key: str, github_token: str, github_repo_name: str) -> str:
    """
    Handles the entire blog post creation process from a single topic line.
    This tool now requires API keys and repo name to be passed explicitly.
    """
    # 1. Parse Keywords
    primary_keyword, secondary_keywords = parse_keywords(topic_line)
    if not primary_keyword:
        return "Error: Could not parse the primary keyword from the topic line."

    # 2. Generate Article
    print(f"Generating article for: {primary_keyword}")
    full_article_content = generate_article(primary_keyword, secondary_keywords, api_key=openai_api_key)
    if "Error:" in full_article_content:
        return full_article_content

    # 3. Assign Category
    print(f"Assigning category for: {primary_keyword}")
    category = assign_category(primary_keyword, api_key=openai_api_key)
    if "Error:" in category:
        return category

    # 4. Create Image
    print(f"Creating image for: {primary_keyword}")
    body_content = "\n".join(full_article_content.split('\n')[2:])
    image_local_path = create_image(body_content, primary_keyword, api_key=openai_api_key)
    if "Error:" in image_local_path:
        return image_local_path

    # 5. Publish to GitHub
    print(f"Publishing post for: {primary_keyword}")
    title = full_article_content.split('\n')[0].strip()
    result = publish_to_github(title, full_article_content, category, image_local_path, token=github_token, repo_name=github_repo_name)
    
    return result

# --- Agent Setup ---

def main():
    """
    Main function to initialize and run the Blog Studio Agent.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo_name = os.getenv("GITHUB_REPO_NAME")

    if not all([openai_api_key, github_token, github_repo_name]):
        print("Error: Required environment variables are not set.")
        print(f"OPENAI_API_KEY is set: {openai_api_key is not None}")
        print(f"GITHUB_TOKEN is set: {github_token is not None}")
        print(f"GITHUB_REPO_NAME is set: {github_repo_name is not None}")
        sys.exit(1)

    tools = [full_blog_creation_pipeline_tool]

    agent_system_prompt = "You are a supervisor AI. Your only job is to take a topic line and pass it to the `full_blog_creation_pipeline_tool`."

    prompt = ChatPromptTemplate.from_messages([
        ("system", agent_system_prompt),
        ("user", "{input}"),
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

    # Pass the environment variables explicitly to the tool
    response = agent_executor.invoke({
        "input": topic_line,
        "openai_api_key": openai_api_key,
        "github_token": github_token,
        "github_repo_name": github_repo_name
    })

    print("--- Agent execution finished ---")
    print(f"Final Output: {response['output']}")
    print("--------------------------------")


if __name__ == "__main__":
    main()
