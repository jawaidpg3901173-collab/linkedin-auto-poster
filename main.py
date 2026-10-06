import os
import sys
import logging
import requests

# Load environment variables from a .env file if available (useful for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_required_env_var(var_name: str) -> str:
    """Retrieve and validate an environment variable."""
    value = os.getenv(var_name)
    if not value or not value.strip():
        logger.error(f"Missing required environment variable: {var_name}")
        sys.exit(1)
    return value.strip()


def generate_linkedin_post(gemini_api_key: str) -> str:
    """Generate an engaging LinkedIn post about business automation using Google Gemini API."""
    logger.info("Initializing Google Gemini API...")
    genai.configure(api_key=gemini_api_key)

    prompt = (
        "You are an experienced business operations and automation consultant. "
        "Write a concise, high-value, and authentic LinkedIn post about automating business tasks.\n\n"
        "Guidelines:\n"
        "- Hook the reader in the first 2 lines with a relatable business challenge or observation.\n"
        "- Share 3-4 practical, actionable insights on how businesses can automate repetitive workflows "
        "(e.g., customer follow-ups, reporting, data sync, email triage, or AI-assisted operations).\n"
        "- Focus on tangible outcomes: hours saved, reduced errors, and freeing teams for strategic growth.\n"
        "- Maintain a professional, approachable, and non-preachy tone.\n"
        "- Do NOT use robotic cliché phrases like 'In today's fast-paced world' or 'Dive in'.\n"
        "- Conclude with a thought-provoking question to invite comments.\n"
        "- Add 3-5 relevant, focused hashtags at the end (e.g., #BusinessAutomation #Productivity #WorkflowOptimization).\n"
        "- Output ONLY the final post text. Do not wrap in markdown code blocks or add introductory text."
    )

    candidate_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    
    for model_name in candidate_models:
        try:
            logger.info(f"Generating content using model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response.text and response.text.strip():
                post_content = response.text.strip()
                # Clean up any surrounding quotes or markdown code block markers if present
                if post_content.startswith("```") and post_content.endswith("```"):
                    lines = post_content.splitlines()
                    post_content = "\n".join(lines[1:-1]).strip()
                logger.info("Successfully generated LinkedIn post content.")
                return post_content
        except Exception as e:
            logger.warning(f"Failed with model {model_name}: {e}. Trying next available model if any...")

    logger.error("Failed to generate content with all attempted Gemini models.")
    sys.exit(1)


def publish_to_linkedin(access_token: str, person_urn: str, post_content: str) -> None:
    """Publish content to LinkedIn using the /rest/posts API endpoint."""
    url = "https://api.linkedin.com/rest/posts"

    # Ensure Person URN is correctly formatted
    formatted_author = person_urn if person_urn.startswith("urn:li:person:") else f"urn:li:person:{person_urn}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202401",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": formatted_author,
        "commentary": post_content,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    logger.info(f"Publishing post to LinkedIn for author: {formatted_author}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        logger.error(f"Network error while contacting LinkedIn API: {e}")
        sys.exit(1)

    if response.status_code == 201:
        post_urn = response.headers.get("x-restli-id", "Unknown ID")
        logger.info(f"Successfully published post to LinkedIn! Post ID: {post_urn}")
    else:
        logger.error(f"Failed to publish to LinkedIn. Status Code: {response.status_code}")
        logger.error(f"Response Body: {response.text}")
        sys.exit(1)


def main():
    logger.info("Starting Daily LinkedIn Post automation script...")

    # Load and validate environment variables
    gemini_api_key = get_required_env_var("GEMINI_API_KEY")
    linkedin_access_token = get_required_env_var("LINKEDIN_ACCESS_TOKEN")
    person_urn = get_required_env_var("PERSON_URN")

    # Generate the post
    post_content = generate_linkedin_post(gemini_api_key)
    logger.info(f"\n--- GENERATED POST PREVIEW ---\n{post_content}\n-----------------------------")

    # Publish the post
    publish_to_linkedin(linkedin_access_token, person_urn, post_content)
    logger.info("Automation process completed successfully.")


if __name__ == "__main__":
    main()
