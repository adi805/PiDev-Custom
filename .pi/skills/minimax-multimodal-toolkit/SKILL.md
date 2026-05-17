---
name: minimax-multimodal-toolkit
description: >
  MiniMax-native multimodal workflow for image, video, voice, music, and media-processing tasks.
  Use when the user asks to generate image/video/audio assets, wants MiniMax-specific media APIs,
  needs TTS or voice workflows, wants reproducible local media outputs, or needs FFmpeg-style
  processing around generated media.
license: MIT
metadata:
  version: "2.0.0"
  category: media-generation
  sources:
    - MiniMax platform media capabilities
    - MiniMax API documentation (platform.minimaxi.com)
    - Current runtime tool surface
    - FFmpeg documentation
    - PIL/Pillow documentation
---

# MiniMax Multimodal Toolkit

Use MiniMax-native media workflows without bloating the always-on prompt. Route the task to the smallest path that can honestly produce the requested artifact. This skill covers the full lifecycle: prompt design, generation, post-processing, delivery, and optimization.

## When to Use

Trigger this skill when the task involves:

- **Image generation**: user asks for a picture, illustration, diagram, photorealistic render, stylized art, or image variation/editing
- **Video generation**: short video clips, animation, motion graphics, video from text or image prompts
- **Text-to-Speech (TTS)**: voice synthesis, narration, audiobook clips, voiceovers, real-time streaming TTS
- **Voice cloning / custom voices**: generating speech in a specific voice, voice design, voice transfer
- **Music generation**: instrumental tracks, background music, song composition, music from text descriptions or reference audio
- **Speech-to-text / audio transcription**: transcribing audio files, real-time speech recognition
- **Multimodal chaining**: combining multiple media types into a single pipeline (e.g., image → video, music + voiceover)
- **Media post-processing**: format conversion, trimming, concatenation, watermarking, resolution/bitrate adjustment, audio normalization
- **Batch generation**: generating many assets programmatically with consistent styling

**Do NOT use this skill** for: text-only tasks, code generation, data analysis, or tasks that don't involve media creation/processing. For those, fall through to general-purpose reasoning or other skills.

**For deep API references, code examples, and performance tuning, also read `reference.md` in this skill directory.**

---

## Quick Decision Tree

```
User asks for media generation
  │
  ├─ Image? ──YES──> Decide: direct tool (existing runtime) OR MiniMax Image API
  │                    → if direct tool available and sufficient: use it
  │                    → if MiniMax-specific quality/style needed: go MiniMax API
  │
  ├─ Video? ──YES──> MiniMax Video API (text-to-video, image-to-video)
  │                    → short clips (<10s) default; longer = stitch multiple
  │
  ├─ Speech/Voice? ──YES──> MiniMax TTS API (speech-2.0-hd or turbo)
  │                           → voice cloning if custom voice needed
  │
  ├─ Music? ──YES──> MiniMax Music API (music-01)
  │                    → instrumental or vocals, specify genre/tempo/mood
  │
  ├─ Transcription? ──YES──> MiniMax Speech-to-Text API
  │
  └─ Multi-step? ──YES──> Chain: generate each piece, then ffmpeg/combine
```

---

## API Routing Matrix

Map user intent to the correct MiniMax API endpoint. Always check current docs for version changes.

### Image Generation → `v1/image/generation`

| Parameter | Details |
|-----------|---------|
| Endpoint | `POST https://api.minimaxi.com/v1/image/generation` |
| Model | `image-01` |
| Key inputs | `prompt` (string), `n` (1-10), `size` (e.g., `1024x1024`), `response_format` (`url` or `b64_json`), `style` (optional) |
| Constraints | Max 10 images per request; prompt length ≤ 4000 chars; NSFW content filtered |
| Rate limit | Varies by plan; typically 50 requests/min for pro tier |
| Typical latency | 2–10 seconds per image |

**Prompting best practices for images:**
- Be descriptive: include subject, action, setting, style, lighting, mood
- Specify aspect ratio explicitly when important
- Use style keywords: `"photorealistic"`, `"oil painting"`, `"cyberpunk"`, `"minimalist"`, `"3D render"`
- Negative prompts: describe what to avoid (supported by some endpoints)

### Video Generation → `v1/video/generation`

| Parameter | Details |
|-----------|---------|
| Endpoint | `POST https://api.minimaxi.com/v1/video/generation` |
| Model | `video-01` |
| Key inputs | `prompt` (string), `duration` (seconds, typical 2-10), `resolution` (`720p`/`1080p`), `fps` (default 24), `image_url` (optional, for image-to-video) |
| Constraints | Max duration 30s per request; resolution limits per tier |
| Rate limit | 10 requests/min (check plan) |
| Typical latency | 30s–2min per video |

**Prompting for video:**
- Describe motion explicitly: camera movement, subject actions, transitions
- Include temporal keywords: `"slow pan"`, `"time-lapse"`, `"smooth tracking shot"`
- For image-to-video, the image becomes the first frame; describe how it should animate

### Text-to-Speech → `v1/t2a_v2` (or `v1/text_to_speech`)

| Parameter | Details |
|-----------|---------|
| Endpoint | `POST https://api.minimaxi.com/v1/t2a_v2` |
| Model | `speech-2.0-hd` (high quality), `speech-2.0-turbo` (faster) |
| Key inputs | `text` (string), `voice_id` (preset voice), `model`, `speed` (0.5–2.0), `pitch` (0.5–2.0), `response_format` (`mp3`, `wav`, `ogg`, `pcm`), `stream` (bool) |
| Constraints | Text length ≤ 5000 chars per request; streaming available for low-latency |
| Rate limit | 30 requests/min |
| Typical latency | 1–5 seconds (turbo), 5–15 seconds (HD) |

**Voice presets:** `male-qn-qingse`, `female-shaonv`, `male-qn-jingying`, `female-yujie`, etc. Check docs for full list.

### Voice Cloning → `v1/voice_clone` (or within TTS API)

| Parameter | Details |
|-----------|---------|
| Endpoint | `POST https://api.minimaxi.com/v1/voice_clone` |
| Key inputs | `audio_file` (reference audio, WAV/MP3, 10–60s), `voice_name` (string) |
| Output | `voice_id` (use in TTS requests) |
| Constraints | Reference audio must be clean, single speaker, minimal background noise |

### Music Generation → `v1/music/generation`

| Parameter | Details |
|-----------|---------|
| Endpoint | `POST https://api.minimaxi.com/v1/music/generation` |
| Model | `music-01` |
| Key inputs | `prompt` (describe genre, instruments, tempo, mood), `duration` (seconds), `reference_audio` (optional, for style transfer) |
| Constraints | Max duration varies (30–120s); lyrics not directly supported |
| Rate limit | 10 requests/min |
| Typical latency | 10–60 seconds |

### Speech-to-Text → `v1/speech_to_text`

| Parameter | Details |
|-----------|---------|
| Endpoint | `POST https://api.minimaxi.com/v1/speech_to_text` |
| Key inputs | `audio_file` (WAV/MP3/OGG/FLAC), `language` (optional auto-detect), `response_format` (`json`, `text`, `srt`, `vtt`) |
| Constraints | File size ≤ 100 MB, duration ≤ 4 hours |

---

## Streaming Patterns

### When to Stream

| Modality | Streaming benefit | When to use |
|----------|-------------------|-------------|
| TTS | Play audio while still generating; lower perceived latency | Real-time voice assistants, live narration, long-form TTS |
| Video | N/A (generation too slow for real-time) | Not applicable |
| Image | N/A (single output) | Not applicable |
| Music | Available on some models | Live music generation for interactive apps |
| Transcription | Real-time speech processing | Live captions, voice commands |

### Streaming TTS Implementation Pattern

```python
import requests
import json

# Streaming TTS request
response = requests.post(
    "https://api.minimaxi.com/v1/t2a_v2",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "speech-2.0-turbo",
        "text": "Your long text here...",
        "voice_id": "male-qn-qingse",
        "stream": True,
        "response_format": "pcm"
    },
    stream=True
)

# Process chunks
for chunk in response.iter_content(chunk_size=4096):
    if chunk:
        # Send to audio output buffer
        audio_buffer.write(chunk)
```

---

## Codec & Format Handling

### Generated Output Formats (by modality)

| Modality | Output formats | Recommended for quality | Recommended for web |
|----------|----------------|-------------------------|---------------------|
| Image | PNG, JPEG, WebP, base64 | PNG (lossless), JPEG quality 95 | WebP (smaller, good quality) |
| Video | MP4 (H.264), MOV | MP4/H.264 1080p high bitrate | MP4/H.264 720p |
| TTS audio | MP3, WAV, OGG, PCM | WAV (lossless) or MP3 320kbps | MP3 128kbps or OGG |
| Music | MP3, WAV | WAV 44.1kHz 16-bit | MP3 320kbps |

### Post-Processing with FFmpeg

Common pipelines after generation:

```bash
# Convert video to lower resolution
ffmpeg -i generated.mp4 -vf scale=1280:720 -c:v libx264 -crf 23 output_720p.mp4

# Extract audio from video
ffmpeg -i generated.mp4 -vn -acodec copy audio_only.mp3

# Combine generated image + TTS audio into video with static image
ffmpeg -loop 1 -i image.png -i audio.mp3 -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest output.mp4

# Concatenate multiple videos
ffmpeg -f concat -safe 0 -i filelist.txt -c copy merged.mp4

# Normalize audio loudness
ffmpeg -i speech.mp3 -af loudnorm=I=-16:LRA=11:TP=-1.5 normalized.mp3

# Trim video to specific segment
ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:10 -c copy trimmed.mp4

# Add watermark/overlay
ffmpeg -i video.mp4 -i watermark.png -filter_complex "overlay=10:10" watermarked.mp4
```

---

## Prompt Engineering Per Modality

### Image Prompt Template

```
[Main subject], [action/pose], [setting/background], [lighting], [style], [additional details], [mood/atmosphere].
```

**Examples:**
- *Photorealistic:* "A serene mountain lake at sunrise, mirror-like reflection of snow-capped peaks, soft golden light, photorealistic, 8K, highly detailed."
- *Stylized:* "A cyberpunk street market at night, neon signs reflecting on wet pavement, crowded with diverse characters, rain, volumetric lighting, digital art, blade runner style."
- *Minimalist:* "A single red balloon floating against a clear blue sky, minimalist, clean composition, high contrast."

### TTS Prompt / Settings

No natural-language prompt; use parameters:
- `speed`: 1.0 is normal. Lower for narration, higher for rapid speech.
- `pitch`: 1.0 is normal. Adjust for character voices.
- `voice_id`: Choose based on use case (male/female, age, tone). Test multiple.

### Music Prompt Template

```
[Genre], [instruments], [tempo] BPM, [mood], [key] key, [duration] seconds, [additional descriptors]
```

**Examples:**
- "Lo-fi hip hop, piano and soft drums, 80 BPM, chill and relaxed, C major, 60 seconds."
- "Epic orchestral, full symphony with choir, 120 BPM, heroic and triumphant, D minor, 30 seconds."
- "Jazz quartet, saxophone lead, walking bass, 140 BPM, upbeat swing, Bb major, 45 seconds."

### Video Prompt Template

```
[Scene description], [camera movement], [subject action], [lighting], [pace], [mood].
```

**Examples:**
- "A drone flying over a misty forest canopy, slow forward motion, birds scattering, soft morning light, serene and mysterious."
- "A chef cooking in a busy kitchen, close-up tracking shot following hands, fast chopping and flames, warm tungsten light, energetic."

---

## Error Handling

### Common Error Codes

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad request (invalid params) | Check prompt length, parameter values, format constraints |
| 401 | Unauthorized | Verify API key, check expiration, regenerate if needed |
| 402 | Payment required / quota exceeded | Check account balance, upgrade plan, wait for reset |
| 403 | Forbidden (content policy) | Prompt may violate content policy; rephrase to avoid sensitive/restricted content |
| 429 | Rate limit exceeded | Implement exponential backoff, reduce concurrency, spread requests |
| 500 | Server error | Retry with backoff; if persistent after 3 attempts, check status page |
| 503 | Service unavailable | Retry after 30–60 seconds; check for maintenance windows |

### Retry Strategy

```python
import time
import requests

def generate_with_retry(prompt, max_retries=3, base_delay=2):
    for attempt in range(max_retries):
        try:
            response = requests.post(endpoint, json={"prompt": prompt}, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                delay = base_delay * (2 ** attempt)  # exponential backoff
                time.sleep(delay)
                continue
            elif response.status_code >= 500:
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    raise Exception(f"Server error after {max_retries} attempts")
            else:
                # Client error — don't retry blindly
                raise Exception(f"Client error {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise
    return None
```

### Content Policy Violations

MiniMax filters:
- NSFW / explicit content
- Violence, gore, hate speech
- Copyright-infringing content (celebrity likeness, trademarked characters)
- Political sensitive content (varies by region)

If generation fails with content policy error, rephrase prompt to be more generic, avoid celebrity names, and use descriptive rather than direct references.

---

## Output Conventions

### File Naming

```
{project}_{modality}_{timestamp}_{descriptor}.{ext}
```

Examples:
- `marketing_image_20260505_hero_banner.png`
- `podcast_tts_20260505_ep12_intro.mp3`
- `game_trailer_video_20260505_teaser.mp4`

### Directory Structure

```
outputs/
├── images/
├── videos/
├── audio/
│   ├── tts/
│   └── music/
└── combined/
```

### Metadata

Always record generation parameters alongside output:
```json
{
  "prompt": "...",
  "model": "image-01",
  "settings": {"size": "1024x1024", "style": "photorealistic"},
  "timestamp": "2026-05-05T14:30:00Z",
  "api_call_id": "gen_abc123",
  "output_file": "output_image.png"
}
```

---

## Multi-Step Pipelines

### Common Chains

1. **Image + TTS → Slideshow Video**
   - Generate images (1 per slide)
   - Generate TTS narration for each slide
   - Combine with ffmpeg: `ffmpeg -loop 1 -i slide1.png -i audio1.mp3 -c:v libx264 -tune stillimage -c:a aac -shortest slide1.mp4`, then concatenate all slides

2. **Music + Voiceover → Podcast Intro**
   - Generate background music (30–60s)
   - Generate TTS voiceover
   - Mix: `ffmpeg -i music.mp3 -i voiceover.mp3 -filter_complex "[1:a]volume=1.5[voice];[0:a][voice]amix=inputs=2:duration=first:dropout_transition=2" output.mp3`

3. **Text → Image → Video (Image-to-Video)**
   - Generate base image from text
   - Feed image to video generation with motion prompt
   - Post-process video

4. **Batch Content Creation**
   - Iterate over list of prompts
   - Generate each asset
   - Save with consistent naming convention
   - Create manifest file

---

## Rate Limiting & Quotas

- **Check usage**: `GET https://api.minimaxi.com/v1/usage` (if available) or dashboard
- **Quota windows**: Typically per-minute, per-day, per-month
- **Concurrency limits**: Varies by plan; default 3–5 concurrent requests
- **Cost optimization**:
  - Use lower resolution for drafts, final quality for production
  - Cache generated assets (don't regenerate identical prompts)
  - Batch when possible (image gen supports n=10)
  - Use turbo models for latency-sensitive, HD for quality-critical

---

## Caching Strategies

```python
import hashlib
import os
import json

def cache_key(prompt, params):
    """Deterministic cache key from prompt + parameters."""
    key_str = json.dumps({"prompt": prompt, **params}, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]

def get_cached_or_generate(prompt, params, generate_fn, cache_dir="./cache"):
    key = cache_key(prompt, params)
    cache_path = os.path.join(cache_dir, f"{key}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    result = generate_fn(prompt, params)
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(result, f)
    return result
```

---

## Security & Content Policy

- **Never hardcode API keys** in generated code; use environment variables or secrets manager
- **Sanitize user-provided prompts** before sending to API if the app is user-facing
- **Age-gate** content where appropriate
- **Respect copyright**: generated content may be subject to platform terms; understand usage rights
- **Log generation metadata** for audit trail (who, when, what prompt, what output)

---

## Integration Quickstarts

### Python: Generate an Image

```python
import requests

api_key = os.environ["MINIMAX_API_KEY"]
response = requests.post(
    "https://api.minimaxi.com/v1/image/generation",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "image-01",
        "prompt": "A cat wearing a wizard hat, digital art",
        "n": 1,
        "size": "1024x1024",
        "response_format": "url"
    }
)
image_url = response.json()["data"][0]["url"]
```

### Python: Generate TTS Audio

```python
response = requests.post(
    "https://api.minimaxi.com/v1/t2a_v2",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "speech-2.0-hd",
        "text": "Hello, welcome to the MiniMax multimodal toolkit.",
        "voice_id": "female-shaonv",
        "speed": 1.0,
        "response_format": "mp3"
    }
)
with open("output.mp3", "wb") as f:
    f.write(response.content)
```

### cURL: Video Generation

```bash
curl -X POST "https://api.minimaxi.com/v1/video/generation" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "video-01",
    "prompt": "A drone shot flying over a tropical beach at sunset",
    "duration": 5,
    "resolution": "1080p"
  }'
```

---

## Anti-Patterns

- Generating assets without caching duplicate prompts (wastes quota)
- Using HD models for draft iterations (use turbo for quick tests)
- Not checking content policy before batch generation (wastes all requests)
- Hardcoding API keys in scripts shared publicly
- Assuming output is ready for production without reviewing quality
- Ignoring rate limits and causing 429 cascades
- Not logging generation parameters alongside outputs (can't reproduce)
- Using image-to-video with an image that doesn't match the motion prompt (results look unnatural)
