import os
import requests
from bs4 import BeautifulSoup
import sys
from urllib.parse import urljoin
import anthropic

api_key = os.getenv("CLAUDE_API_KEY")

client = anthropic.Anthropic(
    api_key=api_key,
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


def get_all_links(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    return links


def get_text_from_page(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()
    except requests.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return None


def save_text_to_file(text, filename):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)


def convert_transcript_to_essay(transcript):
    message_content = (
        "Here is the transcript to rewrite as a well-formatted markdown essay:\n\n"
        "<transcript>\n"
        f"{transcript}\n"
        "</transcript>\n\n"
        "Your goal is to rewrite this transcript into a coherent, well-structured essay, without losing any of the details or information from the original transcript. The rewritten version should be in markdown format.\n\n"
        "To complete this task, follow these steps:\n\n"
        "1. Carefully read through the entire transcript to fully understand the content.\n\n"
        "2. Extract all the key points, facts, ideas, and details discussed in the transcript. Make sure to note any important context around the main points.\n\n"
        "3. Organize the key information you extracted into a logical flow. Group related points together and put the details in a rational order. The essay should have a clear beginning, middle, and end.\n\n"
        "4. Rewrite each section of the transcript in formal, grammatical essay prose. Don't simply copy sentences from the transcript - reformulate the language to be more precise and concise while preserving the meaning. Use full sentences and paragraphs.\n\n"
        "5. Apply markdown formatting to structure the essay. Use headers to delineate major sections, paragraphs to separate ideas, and lists where appropriate. Aim to enhance the readability and visual clarity of the essay.\n\n"
        "6. Carefully review your rewritten markdown essay. Compare it side-by-side to the original transcript. Check that you did not omit any important details or change the meaning of anything that was said. Revise as needed.\n\n"
        "After you have finished rewriting the transcript as a markdown essay, provide your rewritten version inside <rewritten_essay> tags.\n\n"
        "Remember, the key priorities are to retain all the details from the original transcript, while organizing and expressing the content more formally and clearly in proper essay format with markdown styling. Do not leave out anything substantive from the transcript."
    )

    # Send the message to Claude
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0,
        messages=[{"role": "user", "content": message_content}],
    )

    try:
        essay = (
            response.content.split("<rewritten_essay>")[1]
            .split("</rewritten_essay>")[0]
            .strip()
        )
    except IndexError:
        print("Failed to extract essay from response content.")
        return None

    return essay


def generate_essays_from_transcripts(transcript_folder, essay_folder):
    # Create the essay folder if it doesn't exist
    if not os.path.exists(essay_folder):
        os.makedirs(essay_folder)

    # Iterate over each file in the transcript folder
    for filename in os.listdir(transcript_folder):
        if filename.endswith(".txt"):
            # Read the transcript file
            with open(
                os.path.join(transcript_folder, filename), "r", encoding="utf-8"
            ) as file:
                transcript = file.read()

            # Convert the transcript into an essay
            essay = convert_transcript_to_essay(transcript)

            # Generate the essay filename
            essay_filename = f"essay_{os.path.splitext(filename)[0]}.md"

            # Save the essay as a new file
            with open(
                os.path.join(essay_folder, essay_filename), "w", encoding="utf-8"
            ) as file:
                file.write(essay)

            print(f"Essay saved: {essay_filename}")


def main2():
    # Generate essays from transcripts
    transcript_folder = "transcripts"
    essay_folder = "essays"
    generate_essays_from_transcripts(transcript_folder, essay_folder)


def main():
    url = sys.argv[1]
    links = get_all_links(url)

    # Create transcripts directory if it doesn't exist
    if not os.path.exists("transcripts"):
        os.makedirs("transcripts")

    for i, link in enumerate(links):
        full_link = urljoin(url, link)
        text = get_text_from_page(full_link)
        if text:
            filename = os.path.join("transcripts", f"page_{i+1}.txt")
            save_text_to_file(text, filename)
            print(f"Saved text from {full_link} to {filename}")

    # Generate essays from transcripts
    transcript_folder = "transcripts"
    essay_folder = "essays"
    generate_essays_from_transcripts(transcript_folder, essay_folder)


if __name__ == "__main__":
    main()
