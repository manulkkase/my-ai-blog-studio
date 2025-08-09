import os
import sys
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools import tool

# Load environment variables from .env file
load_dotenv()

# --- Tool Imports ---
# Add the tools directory to the system path to ensure imports work
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from topic_fetcher import fetch_topic
from article_generator import generate_article
from category_assigner import assign_category # 새로운 도구 임포트
from image_creator import create_image
from github_publisher import publish_to_github

# --- Tool Definitions ---
# Use the @tool decorator to convert functions into LangChain tools.
# The docstring of each function is crucial as it's the description the agent uses.

@tool
def topic_fetcher_tool() -> str:
    """
    Fetches the next blog topic from the 'topics.txt' file. This must be the first step.
    """
    return fetch_topic()

@tool
def article_generator_tool(topic: str) -> str:
    """
    Generates a high-quality blog post in Markdown format based on a given topic.
    Use this after successfully fetching a topic.
    """
    return generate_article(topic)

@tool
def category_assigner_tool(topic: str) -> str:
    """
    Assigns the most appropriate category to the blog post based on its topic.
    Use this after generating the article content.
    The available categories are: K-Culture & Palaces, Street Food & Night Markets, Mountains & Rice Terraces, Beaches, Bays & Islands, City Vibes & Night-life, Budget Hacks & Transport.
    """
    return assign_category(topic)

@tool
def image_creator_tool(article_content: str, topic: str) -> str:
    """
    Creates a relevant image for the blog post using DALL-E 3 and saves it locally.
    Use this after assigning the category.
    Returns the local file path of the created image.
    """
    return create_image(article_content, topic)

@tool
def github_publisher_tool(title: str, markdown_body: str, image_local_path: str, category: str) -> str:
    """
    Publishes the final article, its image, and its category to the designated GitHub repository.
    This is the final step. It takes the post title, markdown body, local image path, and the assigned category as input.
    Returns the URL of the published blog post.
    """
    return publish_to_github(title, markdown_body, image_local_path, category)


# --- Agent Setup ---

def main():
    """
    Main function to initialize and run the Blog Studio Agent.
    """
    # Check for necessary environment variables
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("GITHUB_TOKEN") or not os.getenv("GITHUB_REPO_NAME"):
        print("오류: 필수 환경 변수(OPENAI_API_KEY, GITHUB_TOKEN, GITHUB_REPO_NAME)가 설정되지 않았습니다.")
        sys.exit(1)

    # Define the list of tools the agent can use
    tools = [
        topic_fetcher_tool,
        article_generator_tool,
        category_assigner_tool, # 도구 목록에 추가
        image_creator_tool,
        github_publisher_tool
    ]

    # Define the system prompt for the agent
    agent_system_prompt = """
    You are 'Blog Studio Agent', an autonomous AI responsible for operating 'The Unfiltered Trail' blog.
    Your goal is to handle the entire content production pipeline from a given topic to final publication on GitHub.
    You must use the provided tools sequentially and logically to achieve this goal.
    
    Here is your new workflow:
    1.  First, get a topic using `topic_fetcher_tool`.
    2.  If you get a valid topic, use it to generate an article with `article_generator_tool`.
    3.  Then, use the topic to determine the correct category with `category_assigner_tool`.
    4.  After that, use the generated article's content and the original topic to create an image with `image_creator_tool`.
    5.  Finally, use all the generated assets (title, body, image path, and category) to publish everything with `github_publisher_tool`.
    
    Always think step-by-step. If a step fails, report the error. If all steps are successful, report the final URL.
    Do not ask for confirmation at any step, proceed with the workflow autonomously.
    """

    # Create the prompt template for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", agent_system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)

    # Create the agent executor, which runs the agent
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Get user input from command line arguments
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = "자기소개 및 역할 확인"
        print(f"명령어가 제공되지 않았습니다. 기본 프롬프트로 실행합니다: '{user_prompt}'")

    print(f"--- Blog Studio Agent를 다음 명령으로 실행합니다 ---")
    print(f"Input: {user_prompt}")
    print("----------------------------------------------------")

    # Invoke the agent
    response = agent_executor.invoke({"input": user_prompt})

    print("--- Agent 실행 완료 ---")
    print(f"Final Output: {response['output']}")
    print("-------------------------")


if __name__ == "__main__":
    main()