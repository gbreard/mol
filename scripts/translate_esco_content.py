#!/usr/bin/env python3
"""
Traduce el contenido scrapeado de ESCO del inglés al español usando Ollama.
"""

import json
import requests
import time

OLLAMA_HOST = "http://172.17.0.1:11434"
MODEL = "qwen2.5:7b"


def translate_text(text, title):
    """Traduce un texto del inglés al español usando Ollama."""
    prompt = f"""Translate the following text from English to Spanish.
This is technical content about ESCO (European Skills, Competences, Qualifications and Occupations classification).
Keep the same structure (paragraphs, bullet points, headings).
Do NOT add any commentary, just return the translated text.
Use formal Spanish (usted, not tú).
Keep technical terms like ESCO, ISCO, ISCED-F, DigComp, EQF, NACE, URI, RDF, SKOS, CSV, API as-is.
Keep proper nouns as-is (European Commission = Comisión Europea).

Text to translate:
{text}"""

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 8192}
            },
            timeout=300
        )
        resp.raise_for_status()
        result = resp.json()
        translated = result.get('response', '').strip()

        # Remove thinking tags if present (qwen3 sometimes adds these)
        if '<think>' in translated:
            import re
            translated = re.sub(r'<think>.*?</think>', '', translated, flags=re.DOTALL).strip()

        return translated
    except Exception as e:
        print(f"  ERROR translating {title}: {e}")
        return None


def main():
    with open('exports/esco_about_scraped.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    pages = data['pages']
    en_pages = [(i, p) for i, p in enumerate(pages) if p['status'] == 'ok']

    print(f"Páginas a traducir: {len(en_pages)}")
    total = len(en_pages)

    translated_count = 0
    failed = []

    for idx, (page_idx, page) in enumerate(en_pages):
        title = page['title']
        content = page['content']
        chars = len(content)

        print(f"[{idx+1}/{total}] {title} ({chars} chars)...", end=' ', flush=True)

        translated = translate_text(content, title)

        if translated and len(translated) > 50:
            pages[page_idx]['content'] = translated
            pages[page_idx]['status'] = 'ok_translated'
            translated_count += 1
            print(f"OK ({len(translated)} chars)")

            # Save incrementally after each successful translation
            data['pages'] = pages
            data['translated_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            with open('exports/esco_about_scraped.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            failed.append(title)
            print(f"FAIL")

        time.sleep(0.5)

    print(f"\nTraducidas: {translated_count}/{total}")
    if failed:
        print(f"Fallaron: {failed}")
    print("JSON actualizado: exports/esco_about_scraped.json")


if __name__ == '__main__':
    main()
