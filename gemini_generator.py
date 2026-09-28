import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Please add it to the .env file."
    )

client = genai.Client(api_key=API_KEY)


def build_prompt(
    document_type,
    parties,
    terms,
    effective_date,
    jurisdiction,
    additional_details
):
    prompt = f"""
You are LegalEase, an AI-assisted legal
document drafting system.

Create a professional and clearly structured
legal document using the information provided.

IMPORTANT RULES:

1. Do not invent names, addresses, dates,
   amounts, laws, registration numbers,
   or other facts.

2. If information is missing, use:

[INFORMATION REQUIRED]

3. Use formal and neutral legal language.

4. Include a clear document title.

5. Include the parties involved.

6. Use numbered clauses.

7. Include the effective date.

8. Include signature sections.

9. Do not claim that the document is
   guaranteed to be legally valid.

10. Do not fabricate laws or legal citations.

11. At the end include:

AI-assisted draft — review by a qualified
legal professional before signing.

12. Return only the document.
Do not use Markdown code fences.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

EFFECTIVE DATE:
{effective_date}

JURISDICTION:
{jurisdiction}

TERMS AND CONDITIONS:
{terms}

ADDITIONAL DETAILS:
{additional_details}
"""
    return prompt


def generate_legal_document(
    document_type,
    parties,
    terms,
    effective_date,
    jurisdiction,
    additional_details=""
):
    prompt = build_prompt(
        document_type,
        parties,
        terms,
        effective_date,
        jurisdiction,
        additional_details
    )

    max_retries = 3
    base_delay = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=5000
                )
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text.strip()

        except Exception as e:
            error_message = str(e)

            # Retry only temporary server/rate-limit errors
            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
                or "500" in error_message
                or "INTERNAL" in error_message
            ):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)

                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {delay} seconds..."
                    )

                    time.sleep(delay)
                    continue

            # Non-temporary error
            raise RuntimeError(
                f"Gemini API error: {error_message}"
            )

    raise RuntimeError(
        "Gemini service is temporarily unavailable. "
        "Please try again later."
    )