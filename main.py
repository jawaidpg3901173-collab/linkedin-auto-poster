import os
import sys
import logging
import time
from datetime import date
import requests

# Load environment variables from a .env file if available (useful for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google import genai
from google.genai import types, errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

CONTACT_BLOCK = (
    "If you're exploring how AI can improve your operations or customer experience, "
    "I would be happy to discuss ideas.\n"
    "Let's connect.\n"
    "saadbinjawaid@gmail.com\n"
    "www.saadbinjawaid.dev"
)

POST_TOPICS = (
    "AI assistants and chatbots for faster, more consistent customer support",
    "RAG and intelligent search for turning company knowledge into useful answers",
    "workflow automation that removes repetitive handoffs and manual data entry",
    "predictive analytics for making better operational decisions",
    "custom AI solutions that fit a business's existing processes",
    "practical AI adoption and how teams can introduce it responsibly",
    "measurable improvements to business operations through AI and automation",
)


def get_required_env_var(var_name: str) -> str:
    """Retrieve and validate an environment variable."""
    value = os.getenv(var_name)
    if not value or not value.strip():
        logger.error(f"Missing required environment variable: {var_name}")
        sys.exit(1)
    return value.strip()


def get_post_topic() -> str:
    """Choose a topic that rotates between scheduled and manual workflow runs."""
    run_number = os.getenv("GITHUB_RUN_NUMBER")
    if run_number and run_number.isdigit():
        topic_index = int(run_number) - 1
    else:
        topic_index = date.today().toordinal()
    return POST_TOPICS[topic_index % len(POST_TOPICS)]


def is_transient_gemini_error(error: Exception) -> bool:
    """Return True when the Gemini error is a 503 Service Unavailable or transient server error."""
    # Specifically catch 503 Service Unavailable errors
    if isinstance(error, errors.APIError) and getattr(error, "code", None) == 503:
        return True
    if isinstance(error, errors.ServerError):
        return True
    error_text = str(error).upper()
    transient_markers = (
        "503",
        "SERVICE UNAVAILABLE",
        "UNAVAILABLE",
        "429",
        "RESOURCE_EXHAUSTED",
        "500",
        "INTERNAL",
        "502",
        "504",
    )
    return any(marker in error_text for marker in transient_markers)


def generate_linkedin_post(gemini_api_key: str) -> str:
    """Generate an engaging LinkedIn post about business automation using Google Gemini API."""
    logger.info("Initializing Google Gemini API...")
    client = genai.Client(api_key=gemini_api_key)
    topic = get_post_topic()
    logger.info("Selected post topic: %s", topic)

    prompt = (
        "You are Saad Bin Jawaid, an AI Engineer and technology leader with 6+ years of "
        "experience in AI, machine learning, and software engineering. "
        "You lead AI initiatives and build practical, scalable solutions that turn business "
        "data into clarity, automate workflows, reduce operational costs, improve customer "
        "experience, and support smarter decisions.\n\n"
        "Write a concise, high-value, and authentic LinkedIn post related only to this work. "
        "Choose one focused topic per post from areas such as AI assistants and chatbots, "
        "RAG and intelligent search, workflow automation, predictive analytics, custom AI "
        "solutions, AI adoption, or measurable improvements to business operations. "
        "Do not invent clients, projects, credentials, statistics, or results that were not "
        "provided. Do not write generic content unrelated to AI, automation, data, software "
        "engineering, or customer experience.\n\n"
        f"For this run, focus specifically on: {topic}. Do not switch to another topic.\n\n"
        "Guidelines:\n"
        "- Hook the reader in the first 2 lines with a relatable business challenge or observation.\n"
        "- Share 3-4 practical, actionable insights that a business can apply.\n"
        "- Explain tangible outcomes such as saved time, lower costs, fewer errors, faster decisions, "
        "better customer support, or confident scaling without making unsupported numerical claims.\n"
        "- Maintain a professional, approachable, and non-preachy tone.\n"
        "- Do NOT use robotic cliché phrases like 'In today's fast-paced world' or 'Dive in'.\n"
        "- Conclude with a thought-provoking question to invite comments.\n"
        "- Add 3-5 relevant, focused hashtags before the contact block "
        "(e.g., #ArtificialIntelligence #BusinessAutomation #CustomerExperience).\n"
        f"- End with this exact contact block, preserving its wording and line breaks:\n{CONTACT_BLOCK}\n"
        "- Output ONLY the final post text. Do not wrap in markdown code blocks or add introductory text."
    )

    # Disable Automatic Function Calling (AFC) to silence any AFC warnings
    generate_config = types.GenerateContentConfig(
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    configured_model = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    model_names = tuple(dict.fromkeys((configured_model, "gemini-2.5-flash", "gemini-2.0-flash")))
    backoff_delays = [10, 30, 60, 90, 120]  # Longer exponential backoff up to 5 retries
    for model_name in model_names:
        for attempt, delay in enumerate([0, *backoff_delays], start=1):
            try:
                logger.info(
                    "Generating content using model: %s (attempt %s/%s)...",
                    model_name,
                    attempt,
                    len(backoff_delays) + 1,
                )
                if delay:
                    time.sleep(delay)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=generate_config,
                )
                if response.text and response.text.strip():
                    post_content = response.text.strip()
                    if post_content.startswith("```") and post_content.endswith("```"):
                        lines = post_content.splitlines()
                        post_content = "\n".join(lines[1:-1]).strip()
                    if not post_content.endswith(CONTACT_BLOCK):
                        post_content = post_content.rstrip() + "\n\n" + CONTACT_BLOCK
                    logger.info("Successfully generated LinkedIn post using %s.", model_name)
                    return post_content
                raise RuntimeError(f"Gemini returned an empty response from {model_name}")
            except Exception as error:
                if is_transient_gemini_error(error) and attempt <= len(backoff_delays):
                    logger.warning(
                        "Transient Gemini error using %s on attempt %s: %s. Retrying...",
                        model_name,
                        attempt,
                        error,
                    )
                    continue
                if is_transient_gemini_error(error) and model_name != model_names[-1]:
                    logger.warning("Model %s remains unavailable; trying the fallback model.", model_name)
                    break
                logger.error("Failed to generate content using %s: %s", model_name, error)
                if not is_transient_gemini_error(error):
                    sys.exit(1)

    logger.error("Failed to generate content with Gemini using all configured models.")
    sys.exit(1)


def publish_to_linkedin(access_token: str, person_urn: str, post_content: str) -> None:
    """Publish content to LinkedIn using the /rest/posts API endpoint."""
    url = "https://api.linkedin.com/rest/posts"

    # Ensure Person URN is correctly formatted
    formatted_author = person_urn if person_urn.startswith("urn:li:person:") else f"urn:li:person:{person_urn}"

    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
        "LinkedIn-Version": "202601",
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
