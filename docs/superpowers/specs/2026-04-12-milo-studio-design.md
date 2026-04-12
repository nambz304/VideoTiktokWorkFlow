# Milo Studio — Design Spec

**Date:** 2026-04-12  
**Channel:** "Sống khoẻ cùng AI"  
**Mascot:** Milo (robot xanh, có sẵn image library)  
**Goal:** TikTok video pipeline — idea to publish, fully controlled, ~$0/tháng  
**CV purpose:** AI Engineering portfolio project

---

## 1. Overview

Milo Studio là web app giúp tạo video TikTok bán tự động cho kênh sức khoẻ + AI. User kiểm soát từng bước qua wizard UI, có AI chatbox để thảo luận/ra lệnh bất kỳ lúc nào. Mỗi video là 1 session — có thể làm dở, tắt máy, quay lại tiếp.

**Target:** 7+ video/tuần, VI + EN, affiliate (thiết bị điện, thực phẩm chức năng)  
**Cost:** ~$0/tháng (free APIs + local processing)

---

## 2. Architecture

### Frontend — Next.js
- `/studio/[sessionId]` — Wizard UI 6 bước
- `/sessions` — Quản lý tất cả sessions
- `/schedule` — Lịch đăng, calendar view

### Backend — FastAPI (Python)
- **Pipeline Engine** — orchestrate 6 bước per session
- **Session Manager** — save/resume state bất kỳ bước
- **Asset Manager** — quản lý Milo image library (tag by emotion)
- **Trend Fetcher** — Google Trends + Reddit scraper
- **TikTok Client** — upload + schedule post via TikTok Content Posting API
- **AI Chat Handler** — relay tới Gemini, context-aware per step

### Database — SQLite
```sql
sessions(id, title, topic, step, status, lang, created_at, updated_at)
scenes(id, session_id, order, script_text, emotion_tag, image_path, audio_path, video_path, approved)
schedule(id, session_id, post_time, caption, hashtags, tiktok_post_id, status)
```

### External Services (all free)
| Service | Usage | Cost |
|---|---|---|
| Gemini 2.0 Flash API | Script gen + AI chat | $0 (1500 req/day) |
| Edge-TTS | Voice VI + EN | $0 |
| FFmpeg | Video assembly local | $0 |
| Google Trends API | Trend research | $0 |
| Reddit public API | Topic context | $0 |
| TikTok Content Posting API | Publish + schedule | $0 |

---

## 3. UI Layout

```
┌─────────────────────────────────────────────────────┐
│  🤖 MILO STUDIO                                      │
│  [1.Trend] ──✓── [2.Scenes] ──●── [3.Images] ──...  │  ← stepper
├─────────────────────────────────────┬───────────────┤
│                                     │               │
│   Step content (current step only)  │  AI Chatbox   │
│                                     │  (Gemini)     │
│                                     │               │
├─────────────────────────────────────┴───────────────┤
│  [← Back]     Step 3/6 · 2/5 approved    [Next →]   │
└─────────────────────────────────────────────────────┘
```

- **Top:** Stepper — tất cả 6 bước, highlight bước hiện tại, done/pending
- **Main left:** UI của bước hiện tại only
- **Right sidebar:** AI chatbox — ra lệnh, hỏi, thảo luận output bất kỳ lúc
- **Bottom:** Back/Forward nav + progress indicator

---

## 4. Pipeline — 6 Bước Per Video

### Bước 1 — Kịch bản (3 sub-steps)

**1A — Trend Research** (~30 giây, auto)
- Sources: Google Trends VI/EN + Reddit r/health + TikTok hashtag scrape
- Filter: liên quan keywords kênh (sức khoẻ, AI, thực phẩm chức năng, thiết bị)
- Output: 5–10 trending topics + search volume + relevance reason

**1B — Thảo luận topic** (user-driven, qua chatbox)
- AI present trending topics với context
- User thảo luận, combine, điều chỉnh angle
- AI confirm topic cuối → user gõ "OK" / click Confirm mới sang 1C

**1C — Gen 2–3 kịch bản** (~20 giây, auto)
- Gemini gen 2–3 scripts cùng topic, khác nhau: tone (funny/serious/story), hook style, CTA
- User đọc, chọn 1, edit trong editor
- User click "OK, qua bước 2" → mới sang Phân cảnh

### Bước 2 — Phân cảnh
- Auto split script → 3–8 scenes
- Mỗi scene: text + timestamp + emotion_tag (happy/explain/surprise/recommend/cta)
- User: reorder, merge, split, edit text
- Approve → sang Bước 3

### Bước 3 — Chọn ảnh Milo
- AI match emotion_tag → ảnh trong library (pre-tagged)
- User: approve / swap từ gallery
- Background: gradient tự động hoặc chọn từ background pack
- Output: image_path per scene

### Bước 4 — Video từng cảnh
- Edge-TTS → audio per scene (vi-VN-NamMinhNeural / en-US-GuyNeural)
- FFmpeg: ken-burns effect (zoom/pan) + caption burn-in (TikTok style, bottom 1/3)
- User: preview từng clip, redo if needed
- Output: scene_N.mp4

### Bước 5 — Ghép video
- FFmpeg concat tất cả scenes + fade transitions
- BGM overlay (Pixabay free music, auto-duck dưới voice)
- **Song song:** Gemini gen caption VI/EN + hashtag pack (trong lúc FFmpeg render)
- User: preview full video, chỉnh âm lượng BGM slider, review/edit caption + hashtag
- Output: final_video.mp4 + caption + hashtag

### Bước 6 — Xuất & Lên lịch
- User: set ngày giờ đăng (calendar picker)
- TikTok API: upload + schedule
- Session status → "scheduled" → "published"

---

## 5. Session State Machine

```
draft → step_1 → step_2 → step_3 → step_4 → step_5 → step_6 → scheduled → published
             ↑_______________________________________↑
             (back bất kỳ bước nào, state preserved)
```

- State lưu SQLite sau mỗi action
- Tắt máy/đóng tab → quay lại đúng bước đang dở
- Mỗi session có: title, topic, ngôn ngữ (VI/EN/cả hai), status

---

## 6. Management Pages

### /sessions
- Grid/list tất cả sessions: draft, in-progress, scheduled, published
- Filter by status, sort by date
- Mỗi session hiện: thumbnail, title, topic, status, bước đang dở (VD: "Đang ở bước 3/6")
- **Click vào session → navigate tới `/studio/[sessionId]`, mở đúng bước đang dở, tiếp tục làm**

### /schedule
- Calendar view — các video đã đăng + sắp đăng
- Click để xem/edit: caption, hashtag, giờ đăng
- Drag-drop để reschedule
- Stats: views, likes (kéo từ TikTok API sau khi đăng)

---

## 7. Milo Image Library

- 1 base image → gen 30–50 poses/expressions một lần (ChatGPT image gen / Kling)
- Tag mỗi ảnh: emotion (happy, think, point, surprise, recommend, wave, sleep, eat, exercise, hold_product, cta)
- Asset Manager: index JSON, serve local, search by tag
- Không cần gen mới mỗi video

---

## 8. Thời gian Per Video

| Bước | Auto | User | Tổng |
|---|---|---|---|
| 1. Trend + Topic + Script | ~1 phút | 3–10 phút | ~5–12 phút |
| 2. Phân cảnh | ~10 giây | 1–3 phút | ~2–4 phút |
| 3. Chọn ảnh | ~5 giây | 2–5 phút | ~2–5 phút |
| 4. Gen video cảnh | ~2–4 phút | 1–3 phút | ~3–7 phút |
| 5. Ghép video | ~1–2 phút | 1–2 phút | ~2–4 phút |
| 6. Xuất & lên lịch | ~30 giây | 1 phút | ~2 phút |
| **Tổng (quen)** | | | **~10–15 phút** |
| **Tổng (lần đầu)** | | | **~20–35 phút** |

---

## 9. Upgrade Path (khi có doanh thu)

| Phase | Upgrade | Cost thêm | Benefit |
|---|---|---|---|
| Launch | Default stack | $0 | Validate kênh |
| 1–2 tháng | Kling AI video animation | +$10–20/tháng | Milo animate thực sự |
| Có revenue | Claude Sonnet script | +$20/tháng | Hook + copy mạnh hơn |
| Scale | FLUX backgrounds | +$5–15/tháng | Visual đẹp hơn |

---

## 10. Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TailwindCSS |
| Backend | FastAPI, Python 3.11+ |
| Database | SQLite (via SQLAlchemy) |
| Video | FFmpeg |
| AI/LLM | Gemini 2.0 Flash (free) |
| TTS | Edge-TTS |
| Publish | TikTok Content Posting API |
| Trend | Google Trends (pytrends) + PRAW (Reddit) |
