import re
import json
import io
import base64
import os
from PIL import Image
from openai import OpenAI
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def get_figure_description_from_openai(image_bytes: bytes) -> str:
    """
    Sends image bytes to the OpenAI GPT-4V (Vision) model and returns a description.
    """
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Provide a concise, short description for this figure."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        return "Description could not be generated."

def process_figures(content_dt: str, content_md: str, page_image_bytes: bytes, page_num: int, images_dir: str) -> tuple[str, str]:
    """
    Finds figures in a document, extracts them, gets a description, saves them, and updates the document.
    """
    figure_matches_dt = list(re.finditer(r"(<figure>.*?</figure>)", content_dt, re.DOTALL))
    image_matches_md = list(re.finditer(r"<!-- image -->", content_md))

    if len(figure_matches_dt) != len(image_matches_md):
        logger.warning(f"Warning: Mismatch in figure count - DocTags: {len(figure_matches_dt)}, Markdown: {len(image_matches_md)}")
        return content_dt, content_md

    if not figure_matches_dt:
        return content_dt, content_md

    logger.info(f"Found {len(figure_matches_dt)} figures to process on page {page_num}")

    page_image = Image.open(io.BytesIO(page_image_bytes))
    page_width, page_height = page_image.size

    for i, (dt_match, md_match) in enumerate(reversed(list(zip(figure_matches_dt, image_matches_md)))):
        figure_index = len(figure_matches_dt) - 1 - i
        full_figure_block = dt_match.group(0)

        loc_numbers = re.findall(r"<loc_(\d+)>", full_figure_block)
        if len(loc_numbers) != 4:
            logger.warning(f"Skipping figure, not 4 loc tags: {full_figure_block}")
            continue
        
        coords = [int(n) / 100.0 for n in loc_numbers]
        x1, y1, x2, y2 = coords

        left, top, right, bottom = (x1 * page_width, (1 - y2) * page_height, x2 * page_width, (1 - y1) * page_height)
        cropped_image = page_image.crop((left, top, right, bottom))

        with io.BytesIO() as output:
            cropped_image.save(output, format="PNG")
            cropped_image_bytes = output.getvalue()

        logger.info(f"Getting description for figure {figure_index} at location: {coords}...")

        try:
            description_text = get_figure_description_from_openai(cropped_image_bytes)
            unique_id = f"pg_{page_num}_fig_{figure_index + 1}"

            # Save the image
            image_path = os.path.join(images_dir, f"{unique_id}.png")
            cropped_image.save(image_path, "PNG")
            logger.info(f"✓ Saved figure image to {image_path}")

            figcaption = f"<figcaption>[figure: {unique_id}]{description_text}</figcaption>"
            new_figure_block = full_figure_block.replace("</figure>", f"{figcaption}</figure>", 1)

            start, end = dt_match.span()
            content_dt = content_dt[:start] + new_figure_block + content_dt[end:]

            image_markdown = f"![{description_text}]<!-- figure: {unique_id} -->"
            md_start, md_end = md_match.span()
            content_md = content_md[:md_start] + image_markdown + content_md[md_end:]

            logger.info(f"✓ Processed figure {figure_index} with ID: {unique_id}")
        except Exception as e:
            logger.error(f"✗ Failed to process figure {figure_index}: {str(e)}", exc_info=True)
            continue

    return content_dt, content_md