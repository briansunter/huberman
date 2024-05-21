import os
import markdown
from fpdf import FPDF, HTMLMixin
import html
from fpdf import FPDF
import requests
from bs4 import BeautifulSoup
import sys
from urllib.parse import urljoin
from openai import OpenAI
import concurrent.futures

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


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
        "7. Remove any advertisements or promotional content that may be present in the transcript.\n\n"
        "8. Remove intro and outro from podcast such as 'Welcome to the podcast' or 'Thanks for joining us' and other outro such as asking to subscribe.\n\n"
        "After you have finished rewriting the transcript as a markdown essay, provide your rewritten version inside <rewritten_essay> tags.\n\n"
        "Remember, the key priorities are to retain all the details from the original transcript, while organizing and expressing the content more formally and clearly in proper essay format with markdown styling. Do not leave out anything substantive from the transcript."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": message_content}],
        max_tokens=4000,
        temperature=0,
    )

    try:
        essay = (
            response.choices[0]
            .message.content.split("<rewritten_essay>")[1]
            .split("</rewritten_essay>")[0]
            .strip()
        )
    except IndexError:
        print("Failed to extract essay from response content.")
        return None

    return essay


def process_transcript(filename, transcript_folder, essay_folder):
    if filename.endswith(".txt"):
        with open(
            os.path.join(transcript_folder, filename), "r", encoding="utf-8"
        ) as file:
            transcript = file.read()

        essay = convert_transcript_to_essay(transcript)
        if essay:
            essay_filename = f"essay_{os.path.splitext(filename)[0]}.md"
            with open(
                os.path.join(essay_folder, essay_filename), "w", encoding="utf-8"
            ) as file:
                file.write(essay)
            print(f"Essay saved: {essay_filename}")


def generate_essays_from_transcripts(transcript_folder, essay_folder):
    if not os.path.exists(essay_folder):
        os.makedirs(essay_folder)

    filenames = os.listdir(transcript_folder)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(
                process_transcript, filename, transcript_folder, essay_folder
            )
            for filename in filenames
        ]
        concurrent.futures.wait(futures)


def main2():
    transcript_folder = "transcripts"
    essay_folder = "essays"
    generate_essays_from_transcripts(transcript_folder, essay_folder)


def main():
    url = sys.argv[1]
    links = get_all_links(url)

    if not os.path.exists("transcripts"):
        os.makedirs("transcripts")

    for i, link in enumerate(links):
        full_link = urljoin(url, link)
        text = get_text_from_page(full_link)
        if text:
            filename = os.path.join("transcripts", f"page_{i+1}.txt")
            save_text_to_file(text, filename)
            print(f"Saved text from {full_link} to {filename}")

    transcript_folder = "transcripts"
    essay_folder = "essays"
    generate_essays_from_transcripts(transcript_folder, essay_folder)


if __name__ == "__main__":
    main()

from fpdf import (
    FPDF,
    HTMLMixin,
)  # Ensure you have fpdf2 installed and imported correctly


class PDF(FPDF, HTMLMixin):
    def chapter_title(self, title):
        self.set_font("helvetica", style="B", size=12)
        self.cell(0, 10, title, ln=True, align="L")
        self.ln(10)

    def chapter_body_html(self, html_content):
        html_content = html_content.replace("—", "--")
        html_content = html_content.replace("₂", "2")
        # ’
        html_content = html_content.replace("’", "'")
        unescaped_html = html.unescape(html_content)  # Correctly unescape HTML entities
        self.write_html(unescaped_html)  # Pass the unescaped HTML to write_html

    def chapter_body(self, body):
        body = body.replace("—", "--")
        body = body.replace("—", "--")
        self.set_font("helvetica", size=12)  # Use a built-in font
        self.multi_cell(0, 10, body)
        self.ln()


def combine_essays_into_pdf(essay_folder, output_pdf):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for filename in sorted(os.listdir(essay_folder)):
        if filename.endswith(".md"):
            with open(
                os.path.join(essay_folder, filename), "r", encoding="utf-8"
            ) as file:
                title = os.path.splitext(filename)[0]
                markdown_text = file.read()
                html_content = markdown.markdown(markdown_text)

            pdf.add_page()
            pdf.chapter_title(title)
            print(f"Processing file: {filename}")
            pdf.chapter_body_html(html_content)

    pdf.output(output_pdf)
    print(f"Combined PDF saved as {output_pdf}")


def main3():
    essay_folder = "essays"
    output_pdf = "combined_essays.pdf"
    combine_essays_into_pdf(essay_folder, output_pdf)
