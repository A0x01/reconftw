#!/usr/bin/env python3
"""Generate reconFTW reports with Google Gemini."""
import os
import argparse
import json
import urllib.request


def gather_results(path, limit=5 * 1024 * 1024):
    parts = []
    for root, _, files in os.walk(path):
        for name in files:
            if name.startswith('.'):
                continue
            fpath = os.path.join(root, name)
            try:
                if os.path.getsize(fpath) > limit:
                    continue
                with open(fpath, 'r', errors='ignore') as fh:
                    parts.append(f"# {os.path.relpath(fpath, path)}\n" + fh.read())
            except Exception:
                continue
    return "\n\n".join(parts)


def generate_report(api_key, prompt, model="gemini-pro"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.load(resp)
    return result["candidates"][0]["content"]["parts"][0]["text"]


def main():
    parser = argparse.ArgumentParser(description="Generate reconFTW report using Gemini")
    parser.add_argument('--results-dir', required=True, help='ReconFTW results directory')
    parser.add_argument('--output-file', required=True, help='Where to write the report')
    parser.add_argument('--model', default='gemini-pro', help='Gemini model to use')
    parser.add_argument('--api-key', default=os.environ.get('GEMINI_API_KEY'), help='Gemini API key')
    parser.add_argument('--report-type', default='bughunter', help='Report profile')
    parser.add_argument('--output-format', default='md', help='Output format')
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit('GEMINI_API_KEY is required')

    data = gather_results(args.results_dir)
    prompt = (
        f"Generate an advanced {args.report_type} report in {args.output_format} format "
        f"from the following reconnaissance data:\n{data}"
    )
    report = generate_report(args.api_key, prompt, args.model)

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    with open(args.output_file, 'w') as f:
        f.write(report)


if __name__ == '__main__':
    main()
