"""Detection module using Google Gemini + supervision to annotate images.

Environment variables:
  GOOGLE_API_KEY - required
  MODEL_NAME - optional override (default gemini-2.5-flash-preview-05-20)
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from PIL import Image
from google import genai
from google.genai import types
import supervision as sv
import time
import random

DEFAULT_MODEL = os.getenv('MODEL_NAME', 'gemini-2.5-flash-preview-05-20')
TEMPERATURE = 0.4

SAFETY_SETTINGS = [
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_ONLY_HIGH",
    ),
]

PROMPT_SUFFIX = (
    ' Output a JSON list of bounding boxes where each entry contains the 2D bounding box in the key "box_2d",'
    ' and the text label in the key "label". Use descriptive labels.'
)


def _get_client() -> genai.Client:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise RuntimeError('GOOGLE_API_KEY not set')
    return genai.Client(api_key=api_key)


RETRY_STATUS = {503, 500}

def _generate_with_retry(client, *, model, contents, config, max_retries=4, base_delay=1.0):
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as e:  # broad to catch API specific exceptions
            msg = str(e)
            retry_flag = False
            for code in RETRY_STATUS:
                if f"{code}" in msg or 'UNAVAILABLE' in msg.upper() or 'overloaded' in msg.lower():
                    retry_flag = True
                    break
            if not retry_flag or attempt == max_retries:
                last_err = e
                break
            sleep_for = base_delay * (2 ** attempt) * (0.8 + random.random() * 0.4)
            print(f"[retry] attempt {attempt+1} failed: {msg} -> sleeping {sleep_for:.2f}s")
            time.sleep(sleep_for)
            last_err = e
    raise last_err


def run_detection(image_path: str, output_dir: str, prompt: Optional[str] = None) -> str:
    """Run detection and save annotated image.

    Returns path to annotated image.
    """
    prompt = (prompt or 'Detect objects.') + PROMPT_SUFFIX

    image = Image.open(image_path)
    width, height = image.size
    target_height = int(1024 * height / width)
    resized_image = image.resize((1024, target_height), Image.Resampling.LANCZOS)

    client = _get_client()

    response = _generate_with_retry(
        client,
        model=DEFAULT_MODEL,
        contents=[resized_image, prompt],
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE,
            safety_settings=SAFETY_SETTINGS,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )

    result_text = response.text

    resolution_wh = image.size
    detections = sv.Detections.from_vlm(
        vlm=sv.VLM.GOOGLE_GEMINI_2_5,
        result=result_text,
        resolution_wh=resolution_wh,
    )

    thickness = sv.calculate_optimal_line_thickness(resolution_wh=resolution_wh)
    text_scale = sv.calculate_optimal_text_scale(resolution_wh=resolution_wh)

    box_annotator = sv.BoxAnnotator(thickness=thickness)
    label_annotator = sv.LabelAnnotator(
        smart_position=True,
        text_color=sv.Color.BLACK,
        text_scale=text_scale,
        text_position=sv.Position.CENTER,
    )

    annotated = image
    for annotator in (box_annotator, label_annotator):
        annotated = annotator.annotate(scene=annotated, detections=detections)

    out_dir = Path(output_dir)
    out_dir.mkdir(exist_ok=True, parents=True)
    out_path = out_dir / (Path(image_path).stem + '_annotated' + Path(image_path).suffix)
    annotated.save(out_path)
    return str(out_path)


def detect_boxes(image_bytes: bytes, prompt: Optional[str] = None):
    """Accept raw image bytes, run detection, return list of {box_2d:[x1,y1,x2,y2], label:str}."""
    from io import BytesIO
    image = Image.open(BytesIO(image_bytes)).convert('RGB')
    print(f"[detect_boxes] image size: {image.size}, prompt: {prompt}")
    width, height = image.size
    target_height = int(1024 * height / width)
    resized_image = image.resize((1024, target_height), Image.Resampling.LANCZOS)
    p = (prompt or 'Detect objects.') + PROMPT_SUFFIX
    client = _get_client()
    response = _generate_with_retry(
        client,
        model=DEFAULT_MODEL,
        contents=[resized_image, p],
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE,
            safety_settings=SAFETY_SETTINGS,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    print('[detect_boxes] model response received')
    result_text = response.text
    detections = sv.Detections.from_vlm(
        vlm=sv.VLM.GOOGLE_GEMINI_2_5,
        result=result_text,
        resolution_wh=image.size,
    )
    out = []
    for i in range(len(detections)):
        x1, y1, x2, y2 = map(float, detections.xyxy[i])
        label = detections.data.get('class_name', [''])[i] if 'class_name' in detections.data else ''
        out.append({"box_2d": [x1, y1, x2, y2], "label": label})
    print(f"[detect_boxes] parsed boxes: {len(out)}")
    return out, image.size


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('-o', '--output-dir', default='annotated')
    parser.add_argument('-p', '--prompt', default='Detect objects.')
    args = parser.parse_args()

    path = run_detection(args.image, args.output_dir, args.prompt)
    print('Annotated saved to', path)
