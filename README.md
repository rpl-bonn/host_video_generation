# host_video_generation

This repository contains a minimal FastAPI application exposing a dummy
video generation service. It mimics the request/response structure of
[vLLM](https://github.com/vllm-project/vllm)'s OpenAI compatible API but
returns placeholder video files instead of text.

## Endpoints

- `POST /generate` – Accepts a JSON body with `prompt`, base64 encoded
  `image`, optional `negative_prompt` and `guidance` fields. Returns the
  path to a generated video file.
- `GET /download/{file_id}` – Download a previously generated dummy MP4
  file.
- `GET /ping` – Basic health‑check that also reports environment
  configuration.

The service does **not** run any actual video generation pipeline. It is
intended for development and integration tests.
