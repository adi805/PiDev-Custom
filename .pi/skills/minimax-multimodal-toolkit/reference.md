# MiniMax Multimodal Toolkit Reference

Use this file when the task needs deeper routing, implementation detail, troubleshooting guidance, performance optimization, or batch processing patterns beyond `SKILL.md`.

## Route Details

### 1. Direct Asset Generation

Use this route when the user explicitly wants an image or other single artifact and the current runtime already exposes a direct generation tool.

Prefer this when:
- The user asks for a one-off asset
- No reusable app integration is required
- The output only needs to exist, not become part of a coded pipeline

Do not force a MiniMax API implementation when a direct tool already satisfies the request.

**Decision heuristic:**
```
Can a direct tool produce an honest artifact?
  ├─ YES → Use the direct tool. Return the output.
  └─ NO  → Check if MiniMax API can. If yes, go to Route 2.
```

### 2. MiniMax API Integration

Use this route when:
- The user explicitly mentions MiniMax
- The product needs image, video, TTS, voice, or music generation inside application code
- The user wants reproducible local scripts or API examples
- Direct tools cannot satisfy the requested medium

**Before implementing:**
1. Check the current docs or platform references when version-sensitive
2. Inspect existing env handling in the repo
3. Identify the smallest successful request the integration can prove

**API base URL:** `https://api.minimaxi.com/v1`
**Auth header:** `Authorization: Bearer $MINIMAX_API_KEY`

### 3. Media Processing

Use this route when generated or user-provided files need:
- Format conversion
- Concatenation
- Trimming
- Frame extraction
- Audio extraction
- Normalization
- Watermarking or overlay
- Resolution/bitrate adjustment

Prefer local, deterministic tooling (FFmpeg, ImageMagick, Pillow) over re-generating media.

---

## Output Discipline

Use a predictable project-local output directory:

```text
minimax-output/
├── images/
├── video/
├── audio/
│   ├── tts/
│   └── music/
├── combined/
├── tmp/
└── metadata/
```

**Rules:**
- Create the output directory before generation or processing
- Keep temp outputs under `tmp/` — clean up after verification
- Name files: `{project}_{modality}_{timestamp}_{descriptor}.{ext}`
- Do not write generated artifacts into the skill directory
- Always save generation metadata alongside output (prompt, model, settings, timestamp)

**Metadata format:**
```json
{
  "prompt": "...",
  "model": "image-01",
  "settings": {"size": "1024x1024", "style": "photorealistic"},
  "timestamp": "2026-05-05T14:30:00Z",
  "api_call_id": "gen_abc123",
  "output_file": "output_image.png",
  "generation_time_ms": 3200
}
```

---

## Auth and Configuration

When MiniMax API access is required:
- Read credentials from environment variables
- Do not paste secrets into code, logs, or chat
- If host or key configuration is missing, stop and ask only for that missing setup

**Common configuration:**
```text
MINIMAX_API_KEY=sk-...
MINIMAX_API_HOST=https://api.minimaxi.com
```

**Verification command:**
```bash
# Test API key validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  "https://api.minimaxi.com/v1/usage"
# Expected: 200
```

If the current docs or environment use different names, follow the authoritative source rather than this example.

---

## Verification Patterns

### Generated asset
Verify:
- The tool returned a concrete artifact, or
- The file exists at the expected path and is non-zero size
- The file can be opened/played without corruption
- Dimensions/duration match the request (±5% tolerance)

### Media processing
Verify:
- Output file exists
- Output extension and container match the request
- Duration or dimensions are reasonable for the requested task
- No quality degradation beyond expected (compare file sizes)

### App integration
Verify:
- One focused request succeeds end-to-end
- The returned artifact URL, bytes, or metadata are wired into the app correctly
- UI claims are checked at the user surface
- Error states are handled gracefully (what shows when generation fails?)

### Batch generation
Verify:
- All expected files exist
- Count matches requested quantity
- Consistent naming convention followed
- Manifest file is accurate
- No partial failures silently ignored

---

## Prompt and Request Shaping

When helping the user craft media requests:
- Ask for medium, tone, format, and length only if they materially affect the result
- Keep prompts concrete: subject, composition, style, pacing, voice, or mood
- Avoid vague defaults such as "make it nice" without extracting one or two meaningful constraints

**Prompt quality checklist:**
- [ ] Subject clearly identified (what/who is being depicted)
- [ ] Action or state described (what is happening)
- [ ] Setting/background specified
- [ ] Style or aesthetic mentioned (photorealistic, illustration, 3D, etc.)
- [ ] Lighting and mood described when relevant
- [ ] Technical specs included (size, duration, format) if critical

---

## Advanced Pipeline Patterns

### Pattern 1: Image + TTS → Slideshow Video

```bash
# Step 1: Generate images (1 per slide)
# Step 2: Generate TTS narration per slide
# Step 3: Combine each image+audio into a video segment
for i in slide_*.png; do
  base=$(basename "$i" .png)
  ffmpeg -loop 1 -i "$i" -i "${base}.mp3" \
    -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
    -pix_fmt yuv420p -shortest "${base}.mp4"
done

# Step 4: Concatenate all slides
printf "file '%s'\n" slide_*.mp4 > filelist.txt
ffmpeg -f concat -safe 0 -i filelist.txt -c copy final_slideshow.mp4
```

### Pattern 2: Music + Voiceover → Mixed Audio

```bash
# Generate background music (30-60s)
# Generate TTS voiceover
# Mix with voiceover boosted + music ducked
ffmpeg -i music.mp3 -i voiceover.mp3 \
  -filter_complex "[1:a]volume=1.5[voice];[0:a]volume=0.4[music];[music][voice]amix=inputs=2:duration=first:dropout_transition=2" \
  output.mp3
```

### Pattern 3: Text → Image → Video (Image-to-Video)

```python
# 1. Generate base image
image_url = generate_image(prompt="A serene mountain lake at sunrise")

# 2. Feed image to video generation with motion prompt
video_url = generate_video(
    prompt="Slow camera pan across the lake, mist rising, golden light shifting",
    image_url=image_url,
    duration=6
)
```

### Pattern 4: Batch Content Creation with Manifest

```python
import json
import time
from pathlib import Path

prompts = [
    {"id": "hero_01", "prompt": "...", "size": "1792x1024"},
    {"id": "hero_02", "prompt": "...", "size": "1024x1024"},
]
manifest = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "items": []}

for item in prompts:
    result = generate_image(item["prompt"], size=item["size"])
    filename = f"{item['id']}_{int(time.time())}.png"
    save_image(result, f"outputs/images/{filename}")
    manifest["items"].append({**item, "output": filename, "url": result["url"]})

with open("outputs/metadata/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
```

### Pattern 5: Streaming TTS Pipeline

```python
import requests
import io

def stream_tts(text, voice_id="male-qn-qingse", output_path="output.mp3"):
    """Stream TTS audio and write to file as chunks arrive."""
    response = requests.post(
        "https://api.minimaxi.com/v1/t2a_v2",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "speech-2.0-turbo",
            "text": text,
            "voice_id": voice_id,
            "stream": True,
            "response_format": "mp3"
        },
        stream=True, timeout=30
    )
    response.raise_for_status()
    
    buffer = io.BytesIO()
    for chunk in response.iter_content(chunk_size=4096):
        if chunk:
            buffer.write(chunk)
    
    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())
    return output_path
```

---

## Troubleshooting Guide

### API Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| HTTP 401 | Invalid or expired API key | Regenerate key at platform.minimaxi.com, update env var |
| HTTP 402 | Quota exhausted or payment required | Check account balance, upgrade plan, wait for quota reset |
| HTTP 403 | Content policy violation | Rephrase prompt to avoid restricted content; use descriptive instead of celebrity names |
| HTTP 429 | Rate limit exceeded | Implement exponential backoff, reduce concurrency |
| HTTP 500/503 | Server error or maintenance | Retry with backoff after 30-60s; check status page if persistent |
| HTTP 400 with "invalid_request" | Malformed parameters | Check parameter types, prompt length (<4000 chars), size format |

### Generation Quality Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Image blurry/low detail | Resolution too low or prompt lacks detail | Increase size, add detail to prompt: "8K, highly detailed, sharp focus" |
| Image doesn't match prompt | Prompt is ambiguous or contradictory | Remove contradictions, prioritize main subject, use concrete descriptors |
| TTS sounds robotic | Using turbo model for quality-critical audio | Switch to `speech-2.0-hd`, reduce speed to 0.9-1.0 |
| TTS speed wrong | `speed` parameter off | Check parameter; 0.5 = half speed, 1.0 = normal, 2.0 = double |
| Video jerky/low FPS | Default FPS too low or duration mismatch | Specify fps=30, check duration parameter |
| Music cuts off early | Duration mismatch | Verify `duration` matches expected length; regenerate with explicit duration |
| Generation timeouts | Network issue or server load | Set request timeout ≥120s for video, ≥60s for music, implement retry |

### Post-Processing Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| FFmpeg "No such file" | Missing input file | Verify generation completed and file exists at path |
| Audio/video sync drift | Variable frame rate or mismatched durations | Add `-vsync cfr` to FFmpeg, verify exact durations before combining |
| Colors look wrong | Color space mismatch | Add `-pix_fmt yuv420p` for video, ensure sRGB for images |
| File too large | Default codec settings | Use `-crf 23` for H.264, `-b:a 128k` for audio |

### Connectivity Issues

```bash
# Test basic connectivity
curl -s -o /dev/null -w "%{http_code}" https://api.minimaxi.com/v1/usage

# Test DNS resolution
dig +short api.minimaxi.com

# Test with timeout
curl -s --max-time 10 -H "Authorization: Bearer $MINIMAX_API_KEY" \
  "https://api.minimaxi.com/v1/usage"
```

### Retry Strategy

```python
import time
import requests
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=2, max_delay=60):
    """Decorator for exponential backoff retry on transient failures."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    response = func(*args, **kwargs)
                    if response.status_code == 200:
                        return response
                    elif response.status_code == 429:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        print(f"Rate limited. Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    elif response.status_code >= 500:
                        if attempt < max_retries - 1:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            time.sleep(delay)
                            continue
                        raise Exception(f"Server error after {max_retries} attempts")
                    else:
                        raise Exception(f"Client error {response.status_code}: {response.text}")
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    raise
            return None
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def generate_with_retry(prompt, **params):
    return requests.post(
        f"{base_url}/image/generation",
        headers=headers,
        json={"model": "image-01", "prompt": prompt, **params},
        timeout=30
    )
```

---

## Performance Optimization

### Cost Optimization Strategies

| Strategy | Savings | When to Use |
|----------|---------|-------------|
| Use lower resolution for drafts | 50-70% | Iterating on concepts, internal reviews |
| Cache generated assets | 100% for repeats | Identical prompts, CI/CD pipelines |
| Batch image generation (n=10) | ~15% vs individual | When you need multiple images with the same settings |
| Use turbo models for latency-sensitive | 40-60% faster | Real-time TTS, interactive apps |
| Use HD models for quality-critical | N/A | Final production assets |
| Compress output files | 50-80% file size | Web delivery, email attachments |

### Latency Benchmarks (approximate)

| Operation | Turbo | Standard | HD |
|-----------|-------|----------|-----|
| Image (1024×1024) | — | 2-10s | — |
| Image (1792×1024) | — | 5-15s | — |
| TTS (<500 chars) | 1-5s | — | 5-15s |
| TTS (streaming, first chunk) | <1s | — | — |
| Video (6s, 1080p) | — | 30s-2min | — |
| Music (30s) | — | 10-60s | — |
| Speech-to-Text (<1 min audio) | — | 2-10s | — |

### Concurrency Limits

- Default: 3-5 concurrent requests per API key
- Pro tier: typically 10 concurrent
- Enterprise: custom limits

**Concurrency pattern:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_batch(prompts, max_workers=3):
    """Generate images in parallel respecting rate limits."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_image, p["prompt"], p.get("size", "1024x1024")): p 
            for p in prompts
        }
        results = []
        for future in as_completed(futures):
            prompt = futures[future]
            try:
                result = future.result(timeout=120)
                results.append({"prompt": prompt, "result": result})
            except Exception as e:
                results.append({"prompt": prompt, "error": str(e)})
        return results
```

### Caching Implementation

```python
import hashlib
import json
import os
from pathlib import Path

class MediaCache:
    """Deterministic cache for media generation results."""
    
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _key(self, prompt, params):
        """Create a deterministic cache key."""
        payload = json.dumps({"prompt": prompt, **params}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
    
    def get(self, prompt, params):
        key = self._key(prompt, params)
        cache_path = self.cache_dir / f"{key}.json"
        if cache_path.exists():
            with open(cache_path) as f:
                cached = json.load(f)
            # Verify cached file still exists
            output_path = cached.get("output_path")
            if output_path and Path(output_path).exists():
                return cached
        return None
    
    def set(self, prompt, params, result, output_path=None):
        key = self._key(prompt, params)
        cache_path = self.cache_dir / f"{key}.json"
        with open(cache_path, "w") as f:
            json.dump({**result, "output_path": output_path, "cached_at": time.time()}, f)
    
    def get_or_generate(self, prompt, params, generate_fn):
        cached = self.get(prompt, params)
        if cached:
            return cached
        result = generate_fn(prompt, **params)
        self.set(prompt, params, result)
        return result
```

---

## Quality Assurance Checklist

Before delivering generated media to the user:

### Image
- [ ] File exists and is >1KB (not an error page)
- [ ] Dimensions match requested size (±5%)
- [ ] Can be opened without corruption
- [ ] Prompt content is reasonably represented
- [ ] No obvious artifacts, glitches, or cutoff
- [ ] No NSFW/content policy violation visible

### Audio (TTS/Music)
- [ ] File plays without corruption
- [ ] Duration is reasonable (not truncated)
- [ ] Audio levels are appropriate (not silent, not clipping)
- [ ] Voice clarity is acceptable (for TTS)
- [ ] Background noise is minimal

### Video
- [ ] File plays without corruption
- [ ] Duration matches request (±10%)
- [ ] Resolution matches request
- [ ] Frame rate is consistent
- [ ] Audio (if present) is synced
- [ ] No rendering artifacts or glitches

### Batch Output
- [ ] Expected count of files generated
- [ ] Consistent naming convention followed
- [ ] No missing files
- [ ] Manifest/catalog is accurate
- [ ] Error files are documented (which failed and why)

---

## Media Processing Recipes

### FFmpeg Common Operations

```bash
# Convert video resolution
ffmpeg -i input.mp4 -vf "scale=1280:720" -c:v libx264 -crf 23 output_720p.mp4

# Extract audio from video
ffmpeg -i input.mp4 -vn -acodec copy audio_only.mp3

# Combine image + audio into video
ffmpeg -loop 1 -i image.png -i audio.mp3 \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -pix_fmt yuv420p -shortest output.mp4

# Concatenate multiple videos (same codec)
printf "file '%s'\n" video1.mp4 video2.mp4 > files.txt
ffmpeg -f concat -safe 0 -i files.txt -c copy merged.mp4

# Normalize audio loudness (EBU R128)
ffmpeg -i input.mp3 -af "loudnorm=I=-16:LRA=11:TP=-1.5" normalized.mp3

# Trim video to specific segment
ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:10 -c copy trimmed.mp4

# Add watermark/overlay
ffmpeg -i video.mp4 -i watermark.png \
  -filter_complex "overlay=10:main_h-overlay_h-10" watermarked.mp4

# Create video from image sequence
ffmpeg -framerate 24 -pattern_type glob -i 'frame_*.png' \
  -c:v libx264 -pix_fmt yuv420p animation.mp4

# Change audio format
ffmpeg -i input.wav -codec:a libmp3lame -b:a 320k output.mp3

# Extract frames from video (1 per second)
ffmpeg -i input.mp4 -vf "fps=1" frame_%04d.png
```

### ImageMagick Common Operations

```bash
# Resize while maintaining aspect ratio
convert input.png -resize 1024x1024 output.png

# Convert format
convert input.png output.jpg

# Add text overlay
convert input.png -gravity southeast \
  -pointsize 24 -fill white -annotate +10+10 "© 2026" output.png

# Create a grid of images
montage img1.png img2.png img3.png img4.png -tile 2x2 -geometry +5+5 grid.png
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Generate Media Assets
on:
  workflow_dispatch:
    inputs:
      prompt:
        description: 'Image generation prompt'
        required: true

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate Image
        env:
          MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
        run: |
          python scripts/generate_image.py \
            --prompt "${{ github.event.inputs.prompt }}" \
            --output assets/generated/
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: generated-media
          path: assets/generated/
```

### Environment Variable Pattern

```python
# scripts/generate_image.py
import os
import sys
import requests

api_key = os.environ.get("MINIMAX_API_KEY")
if not api_key:
    print("Error: MINIMAX_API_KEY not set", file=sys.stderr)
    sys.exit(1)

# ... generation logic
```

---

## Monitoring and Logging

### Essential Metrics to Track

```python
import time
import logging

logger = logging.getLogger("minimax_multimodal")

def generate_with_monitoring(prompt, **params):
    """Generate with timing, success rate, and cost tracking."""
    start = time.time()
    try:
        response = generate_image(prompt, **params)
        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "image_generation_success",
            extra={
                "prompt_length": len(prompt),
                "latency_ms": elapsed_ms,
                "model": params.get("model", "image-01"),
                "size": params.get("size", "1024x1024"),
            }
        )
        return response
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        logger.error(
            "image_generation_failure",
            extra={
                "prompt_length": len(prompt),
                "latency_ms": elapsed_ms,
                "error": str(e),
            }
        )
        raise
```

**Key metrics:**
- Generation latency (p50, p95, p99)
- Success rate (% of requests returning 200)
- Rate limit hits (429 count)
- Cost per generation (track model + size used)
- Cache hit rate (if using caching)

---

## Security & Compliance

- **Never hardcode API keys** in generated code; use environment variables or secrets manager
- **Sanitize user-provided prompts** before sending to API if the app is user-facing
- **Age-gate** content where appropriate
- **Respect copyright**: generated content may be subject to platform terms; understand usage rights before commercial use
- **Log generation metadata** for audit trail (who, when, what prompt, what output)
- **Rate limit** user requests in your application layer (don't rely solely on API rate limits)
- **Validate** output before displaying to users (check for policy violations, corruption)

### Prompt Sanitization

```python
import re

def sanitize_prompt(user_input, max_length=3800):
    """Basic sanitization for user-facing prompt inputs."""
    # Strip control characters
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', user_input)
    # Truncate to safe length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    # Remove potential injection patterns
    sanitized = sanitized.replace('"""', '"')
    return sanitized.strip()
```

---

## Anti-Patterns

- ❌ Building a whole media subsystem before proving one request
- ❌ Hardcoding API keys in examples or committed code
- ❌ Claiming generated output without checking the artifact exists
- ❌ Inventing local scripts that the repo does not contain
- ❌ Using API integration when a direct generation tool is the simpler honest path
- ❌ Generating without saving metadata (you'll need it for debugging later)
- ❌ Making concurrent requests without respecting rate limits
- ❌ Ignoring HTTP error codes and assuming success
- ❌ Generating the same prompt repeatedly without caching
- ❌ Mixing generated and user-uploaded content without clear provenance tracking

---

## Quick Reference Card

```
MINIMAX MULTIMODAL TOOLKIT — QUICK REFERENCE
=============================================
Base URL: https://api.minimaxi.com/v1
Auth: Bearer $MINIMAX_API_KEY

Endpoints:
  Image:  POST /v1/image/generation   (image-01)
  Video:  POST /v1/video/generation   (video-01)
  TTS:    POST /v1/t2a_v2            (speech-2.0-hd / turbo)
  Voice:  POST /v1/voice_clone       
  Music:  POST /v1/music/generation  (music-01)
  STT:    POST /v1/speech_to_text    

Key Limits:
  Image:  max 10 per request, prompt ≤4000 chars
  Video:  max 30s duration
  TTS:    text ≤5000 chars, streaming available
  Music:  30-120s duration

Retry: 429→exponential backoff, 5xx→retry 3x, 4xx→fix and retry
Cache: SHA256(prompt+params) for deterministic dedup
Output: minimax-output/{images,video,audio,combined,tmp}/

Verification: Always check artifact exists, plays, and matches specs.
```