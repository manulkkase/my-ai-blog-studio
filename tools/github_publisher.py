import os
import re
from datetime import datetime
from github import Github, GithubException

def publish_to_github(title: str, full_article_content: str, category: str, image_local_path: str = None, token: str = None, repo_name: str = None) -> str:
    """
    Publishes the final article according to the new, simplified format.
    It extracts tags from the end of the content and handles optional images.
    """
    github_token = token or os.getenv("GITHUB_TOKEN")
    repo_name = repo_name or os.getenv("GITHUB_REPO_NAME")

    if not all([github_token, repo_name]):
        return "Error: GITHUB_TOKEN or GITHUB_REPO_NAME is not set."
    if "Error:" in full_article_content:
        return "Error: Invalid article content provided. Please check the generation step."

    # --- Start of Content & Tag Extraction ---
    lines = full_article_content.strip().split('\n')
    
    # Find the last line that starts with #, which is the tag line
    tag_line = ""
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith("#"):
            tag_line = lines[i].strip()
            # The content is everything before the tag line
            main_content = "\n".join(lines[:i]).strip()
            break
    else: # If no tag line is found
        main_content = full_article_content.strip()

    # The first line of the main content is the title, second is subtitle. The rest is the body.
    content_lines = main_content.split('\n')
    subtitle_and_body = "\n".join(content_lines[1:]).strip()
    # --- End of Content & Tag Extraction ---

    # --- Start of Image Handling ---
    featured_image_path = ""
    if image_local_path and os.path.exists(image_local_path):
        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            
            image_filename = os.path.basename(image_local_path)
            image_repo_path = f"images/{image_filename}"

            with open(image_local_path, 'rb') as f:
                image_content = f.read()
            
            try:
                repo.get_contents(image_repo_path)
            except GithubException as e:
                if e.status == 404:
                    repo.create_file(path=image_repo_path, message=f"feat: Add image {image_filename}", content=image_content)
                    print(f"Image '{image_repo_path}' uploaded.")
                else:
                    raise e
            
            featured_image_path = f"/{image_repo_path}" # Add leading slash for absolute path

        except Exception as e:
            print(f"Warning: Image processing failed: {e}. Proceeding without an image.")
    # --- End of Image Handling ---

    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        now = datetime.now()
        date_for_frontmatter = now.strftime("%Y-%m-%d")
        
        frontmatter_parts = [
            "---",
            f'title: "{title}"',
            f"date: {date_for_frontmatter}",
            f'category: "{category}"'
        ]
        if featured_image_path:
            frontmatter_parts.append(f'featured_image: "{featured_image_path}"')
        frontmatter_parts.append("---")
        frontmatter = "\n".join(frontmatter_parts)

        # Combine for the final markdown file
        full_markdown_content = f"{frontmatter}

{subtitle_and_body}

{tag_line}"

        time_for_filename = now.strftime("%Y-%m-%d-%H%M%S")
        post_filename_base = re.sub(r'[^a-z0-9\s-]', '', title.lower()).strip().replace(' ', '-')
        if not post_filename_base:
            post_filename_base = "new-post"
        post_filename = f"{time_for_filename}-{post_filename_base}.md"
        
        post_repo_path = f"_posts/{post_filename}"

        commit_result = repo.create_file(
            path=post_repo_path,
            message=f"feat: Add post '{title}'",
            content=full_markdown_content.encode('utf-8'),
        )
        created_file = commit_result['content']
        
        return f"Success: Post was published. URL: {created_file.html_url}"

    except GithubException as e:
        if e.status == 422:
             return f"Error: A file at '{post_repo_path}' already exists."
        return f"Error: A GitHub API error occurred (Status: {e.status}) - {e.data}"
    except Exception as e:
        return f"Error: An unexpected error occurred during publishing - {e}"
    finally:
        if image_local_path and os.path.exists(image_local_path):
            try:
                os.remove(image_local_path)
                print(f"Cleaned up temporary image file: '{image_local_path}'")
            except OSError as e:
                print(f"Error cleaning up temp image file: {e}")