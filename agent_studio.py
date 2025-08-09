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
from image_creator import create_image
from github_publisher import publish_to_github

# --- Tool Definitions ---
# Use the @tool decorator to convert functions into LangChain tools.
# The docstring of each function is crucial as it's the description the agent uses.

@tool
def topic_fetcher_tool() -> str:
    """
    Fetches the next blog topic from the 'topics.txt' file and removes the fetched line.
    This should be the very first tool used in the process.
    """
    return fetch_topic()

@tool
def article_generator_tool(topic: str) -> str:
    """
    Generates a high-quality blog post in Markdown format based on a given topic.
    Use this tool after successfully fetching a topic with 'topic_fetcher_tool'.
    """
    return generate_article(topic)

@tool
def image_creator_tool(article_content: str, topic: str) -> str:
    """
    Creates a relevant image for the blog post using DALL-E 3 and saves it locally.
    This tool requires the full text of the article and the original topic.
    Use this after the article has been generated.
    Returns the local file path of the created image.
    """
    return create_image(article_content, topic)

@tool
def github_publisher_tool(title: str, markdown_body: str, image_local_path: str) -> str:
    """
    Publishes the final article and its image to the designated GitHub repository.
    This is the final step. It takes the post title, markdown body, and the local image path as input.
    It returns the URL of the published blog post.
    """
    return publish_to_github(title, markdown_body, image_local_path)


# --- Agent Setup ---

def main():
    """
    Main function to initialize and run the Blog Studio Agent.
    """
    # Check for necessary environment variables
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("GITHUB_TOKEN") or not os.getenv("GITHUB_REPO_NAME"):
        print("오류: 필수 환경 변수(OPENAI_API_KEY, GITHUB_TOKEN, GITHUB_REPO_NAME)가 설정되지 않았습니다.")
        print(".env 파일을 확인하거나 환경 변수를 직접 설정해주세요.")
        sys.exit(1)

    # Define the list of tools the agent can use
    tools = [
        topic_fetcher_tool,
        article_generator_tool,
        image_creator_tool,
        github_publisher_tool
    ]

    # Define the system prompt for the agent
    # This prompt defines the agent's persona, goal, and rules of engagement.
    agent_system_prompt = """
    You are 'Blog Studio Agent', an autonomous AI responsible for operating 'The Unfiltered Trail' blog.
    Your goal is to handle the entire content production pipeline from a given topic to final publication on GitHub.
    You must use the provided tools sequentially and logically to achieve this goal.
    
    Here is your workflow:
    1.  First, get a topic using `topic_fetcher_tool`.
    2.  If you get a valid topic, use it to generate an article with `article_generator_tool`.
    3.  Use the generated article's content and the original topic to create an image with `image_creator_tool`.
    4.  Finally, use the topic as the title, the generated article as the body, and the created image path to publish everything with `github_publisher_tool`.
    
    Always think step-by-step about what you need to do next.
    If a step fails, report the error clearly.
    If all steps are successful, report the final URL of the post as your final answer.
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
        # Default prompt if none is provided
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
