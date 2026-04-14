# Design: Audio + Video Quality Fix — Milo TikTok Pipeline

**Date:** 2026-04-13  
**Status:** Approved

---

## Context

Video output đầu tiên có 2 vấn đề lớn:

1. **Audio**: TTS đọc toàn bộ scene text (gồm mô tả hành động + lời thoại), thay vì chỉ đọc lời Milo nói
2. **Video**: Mỗi cảnh chỉ là 1 ảnh tĩnh nền trắng + zoom nhẹ — thiếu background, thiếu chuyển động, Milo không ăn khớp ngữ cảnh

**Root cause:** `SceneSplitter` prompt quá đơn giản — không tách `dialogue` vs `action`, không đủ thông tin cho video gen. Kiến trúc sprite+composite không scale và giới hạn ở 10 pose cố định.

---

## Decisions

| Vấn đề | Giải pháp |
|--------|-----------|
| Audio | SceneSplitter extract `dialogue` riêng → TTS chỉ đọc dialogue |
| SceneSplitter model | `claude-haiku-4-5-20251001` → `claude-sonnet-4-6` |
| Video gen | FLUX.1 Kontext — gen Milo + BG tích hợp từ ref ảnh + scene action |
| Character ref | User upload 1-3 ảnh + mô tả tính cách, lưu per-character |
| Multi-user | Tiered: Free=Kontext, Pro=Kontext+Style LoRA, Biz=per-char LoRA |
| Background consistency | 3 BG acts (Hook/Main/CTA), fixed seed per video session |

---

## SceneSplitter Output Schema (Mới)

Model: `claude-sonnet-4-6`

```json
{
  "order": 1,
  "act": "hook",
  "action": "Milo nhảy vào màn hình, làm mặt hoảng sợ, vuốt tay",
  "dialogue": "Ê! Bạn đã Follow chưa? Thì Milo cho bạn lý do ngay đây!",
  "emotion": "surprise"
}
```

- `act`: `hook` (scene đầu) | `main` (giữa) | `cta` (1-2 scene cuối)
- `action`: mô tả hành động Milo → dùng làm prompt cho FLUX Kontext
- `dialogue`: lời Milo nói → dùng cho TTS. Fallback: `action` nếu null

---

## FLUX.1 Kontext — Core Image Gen

**API:** `fal-ai/flux-kontext` via fal.ai hoặc Replicate  
**Cost:** ~$0.05/ảnh  
**Approach:** Truyền character ref images + scene action → gen 1 ảnh tích hợp Milo đúng hành động + background phù hợp

### Prompt per scene:
```
Character: {char_description}
Scene: {scene.action}
Style: {channel.style_preset}, TikTok vertical 9:16, no text overlay
Background: {act_background_context}

act_background_context:
  hook → "energetic, eye-catching, dynamic"
  main → "clean, informative, health/wellness setting"  
  cta  → "warm, inviting, product-focused"
```

### Background consistency (3 acts):
- Cùng `style_prefix` + `seed = hash(session_id) % 1000000` cho cả video
- Hook / Main / CTA mỗi act 1 style prompt → $0.05 × 3 ảnh/video (chia cho số cảnh per act)

---

## User Flow

### Onboarding (làm 1 lần, < 2 phút)
1. Tạo channel: tên, chủ đề, TikTok account, language
2. Tạo character: tên + upload 1-3 ảnh ref + mô tả tính cách
3. Sẵn sàng — không cần train, không chờ

### Tạo video (mỗi lần, ~3 phút tổng)
1. Nhập topic
2. AI gen 2-3 kịch bản → user chọn/chỉnh
3. Auto: SceneSplitter (Sonnet) → FLUX Kontext gen từng cảnh (~15s/cảnh)
4. User review, có thể gen lại từng cảnh ($0.05/lần)
5. TTS (dialogue) + merge → xuất video / đăng TikTok

---

## Multi-user Tiered Architecture

| Tier | Image gen | Consistency | Setup/character |
|------|-----------|-------------|-----------------|
| Free | FLUX Kontext | ~90% | $0, tức thì |
| Pro | Kontext + Style LoRA | ~93% | $0 |
| Business | Per-character LoRA | 97%+ | $15 one-time |

---

## Data Model

```
users
  └── channels (topic, tiktok_account, style_preset, lang)
        └── characters (name, personality, ref_image_paths[], char_description, lora_path?)
        └── sessions
              └── scenes (act, action, dialogue, emotion, image_path, audio_path, video_path)
```

### DB changes vs hiện tại:
- **Thêm:** `users`, `channels`, `characters` tables
- **Sửa `sessions`:** thêm `channel_id`, `character_id`
- **Sửa `scenes`:** thêm `act`, `action`, `dialogue` — bỏ `emotion_tag`, `image_path` (giờ là AI-gen path), `poses`

---

## New Services

| Service | File | Purpose |
|---------|------|---------|
| `CharacterManager` | `backend/services/character_manager.py` | Lưu/load character ref, build Kontext prompt |
| `KontextGenerator` | `backend/services/kontext_generator.py` | Gọi FLUX Kontext API, poll result, lưu ảnh |

## Modified Services

| Service | File | Change |
|---------|------|--------|
| `SceneSplitter` | `backend/services/scene_splitter.py` | Sonnet model, new schema |
| `TTSService` | `backend/services/tts_service.py` | Dùng `scene.dialogue` thay `scene.script_text` |
| `VideoAssembler` | `backend/services/video_assembler.py` | Input từ AI-gen image (không còn composite) |
| `AssetManager` | `backend/services/asset_manager.py` | Optional — giữ 10 PNG làm fallback |

## Modified Router

| File | Steps thay đổi |
|------|---------------|
| `backend/routers/pipeline.py` | Step 2: scene schema mới · Step 3: KontextGenerator · Step 4: TTS từ dialogue |

---

## New Dependencies

```
fal-client>=0.5.0    # hoặc replicate>=0.25.0
```

New env vars:
```
FAL_KEY=...          # hoặc REPLICATE_API_TOKEN=r8_...
```

---

## Removed (không cần nữa)

- `rembg` — không cần xóa nền vì Kontext gen ảnh tích hợp
- `assets/milo/transparent/` preprocessing
- PIL composite logic trong VideoAssembler
- 10 Milo pose PNGs (giữ làm fallback optional)

---

## Verification

1. Tạo character với ảnh Milo ref → `character.ref_image_paths` lưu đúng
2. Step 2: scene response có `act`, `action`, `dialogue`
3. Step 3: `KontextGenerator` trả về ảnh Milo đúng hành động trong scene
4. Step 4: audio ngắn hơn, chỉ đọc `dialogue`
5. Final video: Milo đúng hành động từng cảnh, BG tích hợp tự nhiên
6. Gen lại 1 cảnh: image mới trong ~15s
