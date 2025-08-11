import os
import sys
import re
from typing import Tuple, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools import tool

from tools.topic_fetcher import fetch_topic
from tools.article_generator import generate_article
from tools.category_assigner import assign_category
from tools.image_creator import create_image
from tools.github_publisher import publish_to_github
from tools.utils import config

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

# --- Tool Definitions ---

@tool
def full_blog_creation_pipeline_tool(topic_line: str) -> str:
    """
    Handles the entire blog post creation process from a single topic line.
    This tool fetches the topic, generates the article, assigns a category,
    creates an image, and publishes the final post.
    This is the only tool that should be called directly by the agent.
    """
    # 1. Parse Keywords
    primary_keyword, secondary_keywords = parse_keywords(topic_line)
    if not primary_keyword:
        return "Error: Could not parse the primary keyword from the topic line."

    # 2. Generate Article
    print(f"Generating article for: {primary_keyword}")
    full_article_content = generate_article(primary_keyword, secondary_keywords)
    if "Error:" in full_article_content:
        return full_article_content

    # 3. Assign Category
    print(f"Assigning category for: {primary_keyword}")
    category = assign_category(primary_keyword)
    if "Error:" in category:
        return category

    # 4. Create Image
    print(f"Creating image for: {primary_keyword}")
    # Extract body for better image prompt generation
    body_content = "\n".join(full_article_content.split('\n')[2:])
    image_local_path = create_image(body_content, primary_keyword)
    if "Error:" in image_local_path:
        return image_local_path

    # 5. Publish to GitHub
    print(f"Publishing post for: {primary_keyword}")
    # Extract title from the first line of the article
    title = full_article_content.split('\n')[0].strip()
    result = publish_to_github(title, full_article_content, category, image_local_path)
    
    return result

# --- Agent Setup ---

from tools.utils import config

from tools.utils import config

def main():
    """
    Main function to initialize and run the Blog Studio Agent.
    """
    if not all([config.openai_api_key, config.github_token, config.github_repo_name]):
        print("Error: Required environment variables are not set. Check your GitHub Actions secrets.")
        sys.exit(1)

    tools = [full_blog_creation_pipeline_tool]

    agent_system_prompt = """
    You are 'Blog Studio Agent', a supervisor AI. Your only job is to take a topic line and pass it to the `full_blog_creation_pipeline_tool` to handle the entire process.
    First, fetch the topic line from the user input. Then, call the tool with the fetched topic line.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", agent_system_prompt),
        ("user", "Please process the following topic line: {input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, api_key=config.openai_api_key)
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Fetch the topic directly here instead of inside the agent loop
    topic_line = fetch_topic()
    if not topic_line or "처리할 주제가 없습니다" in topic_line:
        print("No topics to process. Exiting.")
        return

    print(f"--- Blog Studio Agent starting with topic ---")
    print(f"Topic: {topic_line}")
    print("----------------------------------------------------")

    response = agent_executor.invoke({"input": topic_line})

    print("--- Agent execution finished ---")
    print(f"Final Output: {response['output']}")
    print("--------------------------------")


if __name__ == "__main__":
    main()
