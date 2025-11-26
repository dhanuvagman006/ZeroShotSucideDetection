
from __future__ import annotations

import base64
import json
import os
import random
import time
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence

import requests
import supervision as sv
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv('MODEL_NAME', 'gemini-2.0-flash')
TEMPERATURE = 0.4
API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
]

PROMPT_SUFFIX = (
    ' Output a JSON list of bounding boxes where each entry contains the 2D bounding box in the key "box_2d",'
    ' and the text label in the key "label". Use descriptive labels.'
)

RISK_PROMPT = (
    "You are a safety pattern screening assistant. Given an image, you will output a JSON object ONLY. "
    "The JSON must have keys: score (float 0-1), indicators (array of short lowercase strings). "
    "score expresses confidence that the image contains concerning self-harm related visual patterns or tools. "
    "If no concerning patterns: score=0 and indicators=[]. Do not add explanations or extra keys."
)
API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _api_key() -> str:
    key = os.getenv('GOOGLE_API_KEY')
    if not key:
        raise RuntimeError('GOOGLE_API_KEY not set')
    return key


def _model_url() -> str:
    custom = os.getenv('GENAI_MODEL_URL')
    if custom:
        return custom
    return API_URL_TEMPLATE.format(model=DEFAULT_MODEL)


def _image_to_b64(image: Image.Image) -> str:
    buf = BytesIO()
    image.convert('RGB').save(buf, format='JPEG', quality=90)
    return base64.b64encode(buf.getvalue()).decode('ascii')


def _extract_text(data: dict) -> str:
    candidates = data.get('candidates') or []
    for candidate in candidates:
        content = candidate.get('content') or {}
        parts = content.get('parts') or []
        texts = [part.get('text', '') for part in parts if part.get('text')]
        merged = ''.join(texts).strip()
        if merged:
            return merged
    raise RuntimeError('Model response missing text output')


def _parse_json_payload(text: str) -> dict:
    cleaned = (text or '').strip()
    if not cleaned:
        raise ValueError('Empty response text')
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            snippet = cleaned[start:end + 1]
            return json.loads(snippet)
        raise


def _call_model(parts: Sequence[dict], *, temperature: float, max_output_tokens: int = 2048) -> str:
    payload = {
        'contents': [
            {
                'role': 'user',
                'parts': list(parts),
            }
        ],
        'safetySettings': SAFETY_SETTINGS,
        'generationConfig': {
            'temperature': temperature,
            'topP': 0.95,
            'topK': 32,
            'maxOutputTokens': max_output_tokens,
        },
    }
    url = f"{_model_url()}?key={_api_key()}"
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=90)
    if response.status_code >= 400:
        try:
            error = response.json().get('error', {})
        except ValueError:
            error = {}
        message = error.get('message') or response.text
        code = error.get('code', response.status_code)
        raise RuntimeError(f"{code} {message}")
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError('Invalid JSON response from model') from exc
    return _extract_text(data)


RETRY_STATUS = {503, 500}


def _generate_with_retry(parts: Sequence[dict], *, temperature: float, max_retries: int = 4) -> str:
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return _call_model(parts, temperature=temperature)
        except Exception as err:
            msg = str(err)
            retry_flag = False
            for code in RETRY_STATUS:
                if f"{code}" in msg or 'UNAVAILABLE' in msg.upper() or 'OVERLOADED' in msg.upper():
                    retry_flag = True
                    break
            if not retry_flag or attempt == max_retries:
                last_err = err
                break
            sleep_for = (2 ** attempt) * (0.8 + random.random() * 0.4)
            print(f"[retry] attempt {attempt + 1} failed: {msg} -> sleeping {sleep_for:.2f}s")
            time.sleep(sleep_for)
            last_err = err
    raise last_err  # type: ignore[misc]


def _parts_for_image(prompt: str, image: Image.Image) -> list[dict]:
    return [
        {'text': prompt},
        {
            'inline_data': {
                'mime_type': 'image/jpeg',
                'data': _image_to_b64(image),
            }
        },
    ]


def run_detection(image_path: str, output_dir: str, prompt: Optional[str] = None) -> str:
    prompt_text = (prompt or 'Detect objects.') + PROMPT_SUFFIX

    image = Image.open(image_path)
    width, height = image.size
    target_height = int(1024 * height / width)
    resized_image = image.resize((1024, target_height), Image.Resampling.LANCZOS)

    result_text = _generate_with_retry(
        _parts_for_image(prompt_text, resized_image),
        temperature=TEMPERATURE,
    )

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
    image = Image.open(BytesIO(image_bytes)).convert('RGB')
    print(f"[detect_boxes] image size: {image.size}, prompt: {prompt}")
    width, height = image.size
    target_height = int(1024 * height / width)
    resized_image = image.resize((1024, target_height), Image.Resampling.LANCZOS)
    p = (prompt or 'Detect objects.') + PROMPT_SUFFIX
    result_text = _generate_with_retry(
        _parts_for_image(p, resized_image),
        temperature=TEMPERATURE,
    )
    print('[detect_boxes] model response received')
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


def assess_risk(image_bytes: bytes) -> dict:
    image = Image.open(BytesIO(image_bytes)).convert('RGB')
    width, height = image.size
    target_height = int(512 * height / width)
    resized_image = image.resize((512, target_height), Image.Resampling.LANCZOS)
    try:
        result_text = _generate_with_retry(
            _parts_for_image(RISK_PROMPT, resized_image),
            temperature=0.1,
        )
        data = _parse_json_payload(result_text)
        score = float(data.get('score', 0))
        indicators = data.get('indicators', []) or []
        if not isinstance(indicators, list):
            indicators = []
        indicators = [str(x)[:40].lower() for x in indicators][:10]
        score = max(0.0, min(1.0, score))
        return {'score': score, 'indicators': indicators, 'raw': result_text}
    except Exception as e:  # noqa
        print('[assess_risk] failed:', e)
        if 'result_text' in locals():
            preview = (result_text or '')[:240]
            print('[assess_risk] raw response preview:', preview)
        return {'score': 0.0, 'indicators': [], 'raw': None}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('-o', '--output-dir', default='annotated')
    parser.add_argument('-p', '--prompt', default='Detect objects.')
    args = parser.parse_args()

    path = run_detection(args.image, args.output_dir, args.prompt)
    print('Annotated saved to', path)
