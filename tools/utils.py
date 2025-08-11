import os

class Config:
    """
    A centralized configuration class to hold all environment variables.
    """
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo_name = os.getenv("GITHUB_REPO_NAME")

        if not all([self.openai_api_key, self.github_token, self.github_repo_name]):
            print("Error: One or more required environment variables are not set.")
            print(f"OPENAI_API_KEY: {'SET' if self.openai_api_key else 'NOT SET'}")
            print(f"GITHUB_TOKEN: {'SET' if self.github_token else 'NOT SET'}")
            print(f"GITHUB_REPO_NAME: {self.github_repo_name or 'NOT SET'}")
            # In a real-world scenario, you might want to raise an exception here.
            # For the workflow, we'll let the individual tools handle the error message.

# Create a single, global instance of the Config class.
# Other modules will import this instance.
config = Config()
