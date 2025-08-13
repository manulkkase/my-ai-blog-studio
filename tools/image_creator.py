import os
import re
import requests
from datetime import datetime

def create_image(article_content: str, topic: str) -> str:
    """
    Searches for a relevant, high-quality image from Pixabay based on the topic,
    downloads it, and saves it to a local path.
    """
    pixabay_api_key = os.getenv("PIXABAY_API_KEY")
    if not pixabay_api_key:
        return "Error: PIXABAY_API_KEY is not set."

    # Use the primary keyword (topic) as the search query
    search_query = topic
    
    # Pixabay API URL
    url = "https://pixabay.com/api/"
    params = {
        "key": pixabay_api_key,
        "q": search_query,
        "image_type": "photo",
        "orientation": "horizontal",  # Prefer landscape images for blog covers
        "safesearch": "true",
        "per_page": 10  # Get a few options to choose from
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        if not data["hits"]:
            return f"Error: No images found on Pixabay for '{search_query}'."

        # Select the best image (e.g., the one with the most likes or downloads)
        best_image = max(data["hits"], key=lambda x: x.get("likes", 0))
        image_url = best_image.get("largeImageURL")

        if not image_url:
            return "Error: Could not retrieve image URL from Pixabay."

        # Generate a unique filename based on the topic
        file_name_base = re.sub(r'[^a-z0-9\s-]', '', topic.lower()).strip()
        file_name_base = re.sub(r'\s+', '-', file_name_base)
        if not file_name_base:
            file_name_base = "blog-post"
        
        timestamp = datetime.now().strftime("%H%M%S")
        file_name = f"{file_name_base}-{timestamp}.jpg"
        image_path = file_name

        # Download and save the image
        img_data = requests.get(image_url).content
        with open(image_path, 'wb') as handler:
            handler.write(img_data)

        return image_path

    except requests.exceptions.RequestException as e:
        return f"Error: Failed to connect to Pixabay API - {e}"
    except Exception as e:
        return f"Error: An unexpected error occurred while fetching the image - {e}"

if __name__ == '__main__':
    # For standalone testing
    test_topic = "Korean BBQ"
    # This test requires a PIXABAY_API_KEY in the environment
    if os.getenv("PIXABAY_API_KEY"):
        image_path_result = create_image("Test content", test_topic)
        print(f"--- Image Creator (Pixabay) Result ---")
        print(f"Image saved at: {image_path_result}")
        if "Error:" not in image_path_result and os.path.exists(image_path_result):
            print("Verification: Image file created successfully.")
        else:
            print("Verification: Image file creation failed.")
    else:
        print("Please set the PIXABAY_API_KEY environment variable for testing.")
