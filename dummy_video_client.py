"""dummy_video_client.py
Blocking command-line client for dummy_video_service.py.

Example
-------
python dummy_video_client.py \
    --server http://localhost:8002 \
    --prompt "Loop this please" \
    --image image.jpg 
"""

import argparse
import base64
import pathlib
import sys
import json
import requests


def make_data_uri(image_path: pathlib.Path) -> str:
    """Return a data-URI (`data:image/…;base64,…`)."""
    mime = {
        ".jpg":  "jpeg",
        ".jpeg": "jpeg",
        ".png":  "png",
        ".gif":  "gif",
    }.get(image_path.suffix.lower())
    if mime is None:
        raise ValueError("Unsupported image extension: " + image_path.suffix)
    return (
        f"data:image/{mime};base64,"
        + base64.b64encode(image_path.read_bytes()).decode()
    )


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://localhost:8001")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--image",  type=pathlib.Path)
    parser.add_argument("--out",    type=pathlib.Path,
                        default=pathlib.Path("result.mp4"))
    args = parser.parse_args(argv)

    # Build OpenAI-style request payload
    content = [{"type": "text", "text": args.prompt}]
    if args.image:
        if not args.image.exists():
            sys.exit(f"Image not found: {args.image}")
        content.append({
            "type": "image_url",
            "image_url": {"url": make_data_uri(args.image)},
        })

    payload = {
        "model": "dummy-video-001",
        "messages": [{"role": "user", "content": content}],
    }

    # POST /v1/chat/completions
    endpoint = args.server.rstrip("/") + "/v1/chat/completions"
    try:
        r = requests.post(endpoint, json=payload, timeout=60)
        r.raise_for_status()
    except requests.RequestException as e:
        sys.exit(f"Request failed: {e}")

    try:
        data = r.json()
    except json.JSONDecodeError:
        sys.exit(f"Invalid JSON: {r.text[:200]}…")

    try:
        video_url = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        sys.exit(f"Unexpected response: {e}\n{json.dumps(data, indent=2)}")

    print("Video URL:", video_url)

    # GET /download/…
    try:
        dl = requests.get(video_url, timeout=60)
        dl.raise_for_status()
        args.out.write_bytes(dl.content)
        print("Downloaded →", args.out.resolve())
    except requests.RequestException as e:
        sys.exit(f"Download failed: {e}")


if __name__ == "__main__":  # pragma: no cover
    main()
