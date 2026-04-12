# Milo Studio — Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Next.js 14 web UI for Milo Studio — wizard pipeline (6 steps), sessions management page, and schedule calendar page.

**Architecture:** Next.js 14 App Router. Each wizard step is a self-contained React component. Session state fetched from FastAPI backend via `lib/api.ts`. ChatSidebar present on all studio pages. No global state management library — React `useState` + `useEffect` + SWR for server state.

**Tech Stack:** Next.js 14, TailwindCSS, SWR, date-fns, @hello-pangea/dnd (drag-drop schedule), TypeScript

**Prerequisite:** Backend running at `http://localhost:8000`

---

## File Structure

```
frontend/
├── app/
│   ├── layout.tsx                  # Root layout, global font/styles
│   ├── page.tsx                    # Redirect → /sessions
│   ├── sessions/
│   │   └── page.tsx                # Sessions grid page
│   ├── studio/
│   │   └── [sessionId]/
│   │       └── page.tsx            # Wizard page — loads session, renders active step
│   └── schedule/
│       └── page.tsx                # Schedule calendar page
├── components/
│   ├── Stepper.tsx                 # Top progress bar (6 steps)
│   ├── ChatSidebar.tsx             # AI chatbox sidebar
│   ├── NavBar.tsx                  # Back/Forward nav + step indicator
│   ├── SessionCard.tsx             # Card in /sessions grid
│   ├── ScheduleCalendar.tsx        # Calendar + list view for schedule
│   └── steps/
│       ├── Step1Trend.tsx          # 1A trends + 1B topic chat + 1C script select
│       ├── Step2Scenes.tsx         # Scene list, reorder, edit, approve
│       ├── Step3Images.tsx         # Image picker per scene
│       ├── Step4Video.tsx          # Per-scene video gen + preview
│       ├── Step5Merge.tsx          # Final video preview + caption edit
│       └── Step6Publish.tsx        # Schedule picker + publish
├── lib/
│   ├── api.ts                      # Typed fetch wrappers for all backend endpoints
│   └── types.ts                    # Shared TypeScript types
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── next.config.ts
```

---

## Task 1: Project Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/next.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: Bootstrap Next.js project**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
```

- [ ] **Step 2: Install additional dependencies**

```bash
cd frontend
npm install swr date-fns @hello-pangea/dnd
npm install -D @types/node
```

- [ ] **Step 3: Update next.config.ts to proxy API**

```typescript
// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 4: Update app/layout.tsx**

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Milo Studio",
  description: "TikTok video pipeline for Sống khoẻ cùng AI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 5: Create app/page.tsx (redirect)**

```typescript
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/sessions");
}
```

- [ ] **Step 6: Verify dev server starts**

```bash
npm run dev
```

Expected: `http://localhost:3000` redirects to `/sessions` (404 OK for now — page not created yet).

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: Next.js 14 project scaffold with Tailwind + SWR"
```

---

## Task 2: Types + API Client

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Create lib/types.ts**

```typescript
export type SessionStatus = "draft" | "in_progress" | "scheduled" | "published";

export interface Session {
  id: number;
  title: string;
  topic: string | null;
  lang: string;
  step: number;
  status: SessionStatus;
  created_at: string;
  updated_at: string | null;
}

export interface Scene {
  id: number;
  session_id: number;
  order: number;
  script_text: string;
  emotion_tag: string | null;
  image_path: string | null;
  audio_path: string | null;
  video_path: string | null;
  approved: boolean;
}

export interface ScheduleEntry {
  id: number;
  session_id: number;
  post_time: string;
  caption: string | null;
  hashtags: string | null;
  tiktok_post_id: string | null;
  status: string;
}

export interface TrendTopic {
  topic: string;
  score: number;
  source: string;
}

export interface MiloImage {
  filename: string;
  tags: string[];
  path: string;
}

export interface ChatMessage {
  role: "user" | "ai";
  text: string;
  timestamp: number;
}
```

- [ ] **Step 2: Create lib/api.ts**

```typescript
const BASE = "/api";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

// Sessions
export const createSession = (title: string, lang: string) =>
  req<import("./types").Session>("/sessions", {
    method: "POST",
    body: JSON.stringify({ title, lang }),
  });

export const listSessions = () =>
  req<import("./types").Session[]>("/sessions");

export const getSession = (id: number) =>
  req<import("./types").Session>(`/sessions/${id}`);

export const updateSession = (id: number, data: Partial<import("./types").Session>) =>
  req<import("./types").Session>(`/sessions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteSession = (id: number) =>
  req<{ ok: boolean }>(`/sessions/${id}`, { method: "DELETE" });

// Pipeline steps
export const fetchTrends = (sessionId: number) =>
  req<import("./types").TrendTopic[]>(`/sessions/${sessionId}/step/1a`, { method: "POST" });

export const generateScripts = (sessionId: number) =>
  req<{ scripts: string[] }>(`/sessions/${sessionId}/step/1c`, { method: "POST" });

export const splitScenes = (sessionId: number, script: string) =>
  req<{ scenes: import("./types").Scene[] }>(`/sessions/${sessionId}/step/2`, {
    method: "POST",
    body: JSON.stringify({ script }),
  });

export const assignImages = (sessionId: number) =>
  req<{ scenes: import("./types").Scene[] }>(`/sessions/${sessionId}/step/3`, { method: "POST" });

export const genSceneVideo = (sessionId: number, sceneId: number) =>
  req<{ scene_id: number; video_path: string }>(`/sessions/${sessionId}/step/4/${sceneId}`, { method: "POST" });

export const mergeVideo = (sessionId: number, bgmPath: string, bgmVolume: number) =>
  req<{ final_video_path: string; caption: string; hashtags: string[] }>(
    `/sessions/${sessionId}/step/5`,
    { method: "POST", body: JSON.stringify({ bgm_path: bgmPath, bgm_volume: bgmVolume }) }
  );

// Scenes
export const getScenes = (sessionId: number) =>
  req<import("./types").Scene[]>(`/sessions/${sessionId}/scenes`);

// Assets
export const listMiloImages = (tag?: string) =>
  req<import("./types").MiloImage[]>(`/assets/milo${tag ? `?tag=${tag}` : ""}`);

// Schedule
export const listSchedule = () =>
  req<import("./types").ScheduleEntry[]>("/schedule");

export const createSchedule = (data: {
  session_id: number;
  post_time: string;
  caption?: string;
  hashtags?: string;
}) =>
  req<import("./types").ScheduleEntry>("/schedule", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateSchedule = (id: number, data: Partial<import("./types").ScheduleEntry>) =>
  req<import("./types").ScheduleEntry>(`/schedule/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

// Chat
export const sendChat = (sessionId: number, message: string, step: number) =>
  req<{ reply: string }>("/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message, step }),
  });
```

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/
git commit -m "feat: TypeScript types + typed API client for all backend endpoints"
```

---

## Task 3: Shared UI Components

**Files:**
- Create: `frontend/components/Stepper.tsx`
- Create: `frontend/components/NavBar.tsx`
- Create: `frontend/components/ChatSidebar.tsx`

- [ ] **Step 1: Create components/Stepper.tsx**

```typescript
"use client";

const STEPS = [
  { n: 1, label: "Kịch bản" },
  { n: 2, label: "Phân cảnh" },
  { n: 3, label: "Chọn ảnh" },
  { n: 4, label: "Video cảnh" },
  { n: 5, label: "Ghép video" },
  { n: 6, label: "Xuất & Đăng" },
];

export default function Stepper({ currentStep }: { currentStep: number }) {
  return (
    <div className="flex items-center gap-0 px-6 py-3 bg-gray-900 border-b border-gray-800">
      {STEPS.map((step, i) => {
        const done = step.n < currentStep;
        const active = step.n === currentStep;
        return (
          <div key={step.n} className="flex items-center flex-1">
            <div className="flex items-center gap-1.5 min-w-0">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 border-2 transition-all
                  ${done ? "bg-emerald-900 border-emerald-400 text-emerald-400" : ""}
                  ${active ? "bg-blue-700 border-blue-400 text-white shadow-[0_0_12px_rgba(59,130,246,0.4)]" : ""}
                  ${!done && !active ? "bg-gray-800 border-gray-600 text-gray-500" : ""}
                `}
              >
                {done ? "✓" : step.n}
              </div>
              <span
                className={`text-xs truncate
                  ${done ? "text-emerald-400" : ""}
                  ${active ? "text-blue-300 font-semibold" : ""}
                  ${!done && !active ? "text-gray-500" : ""}
                `}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-0.5 flex-1 mx-2 ${done ? "bg-emerald-800" : "bg-gray-800"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Create components/NavBar.tsx**

```typescript
"use client";

interface NavBarProps {
  step: number;
  totalSteps: number;
  approvedCount?: number;
  totalCount?: number;
  onBack: () => void;
  onNext: () => void;
  nextDisabled?: boolean;
  nextLabel?: string;
}

export default function NavBar({
  step, totalSteps, approvedCount, totalCount,
  onBack, onNext, nextDisabled, nextLabel,
}: NavBarProps) {
  return (
    <div className="flex items-center gap-3 px-6 py-3 bg-gray-900 border-t border-gray-800 flex-shrink-0">
      <button
        onClick={onBack}
        disabled={step === 1}
        className="px-4 py-1.5 rounded-lg border border-gray-700 bg-gray-800 text-gray-300 text-sm
          hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        ← Bước trước
      </button>

      <span className="text-xs text-gray-500 flex-1 text-center">
        Bước {step} / {totalSteps}
        {approvedCount !== undefined && totalCount !== undefined && (
          <> · {approvedCount}/{totalCount} đã approve</>
        )}
      </span>

      <button
        onClick={onNext}
        disabled={nextDisabled}
        className="px-4 py-1.5 rounded-lg bg-blue-700 border border-blue-500 text-white text-sm font-medium
          hover:bg-blue-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        {nextLabel ?? "Tiếp theo →"}
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Create components/ChatSidebar.tsx**

```typescript
"use client";
import { useState, useRef, useEffect } from "react";
import { sendChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface ChatSidebarProps {
  sessionId: number;
  step: number;
}

export default function ChatSidebar({ sessionId, step }: ChatSidebarProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "ai", text: "Xin chào! Tôi là Milo. Bạn cần hỗ trợ gì không?", timestamp: Date.now() },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text, timestamp: Date.now() }]);
    setLoading(true);
    try {
      const { reply } = await sendChat(sessionId, text, step);
      setMessages((prev) => [...prev, { role: "ai", text: reply, timestamp: Date.now() }]);
    } catch {
      setMessages((prev) => [...prev, { role: "ai", text: "Lỗi kết nối, thử lại nhé.", timestamp: Date.now() }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-72 bg-gray-950 border-l border-gray-800 flex flex-col flex-shrink-0">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-sm font-semibold text-emerald-400">Milo AI</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[90%] px-3 py-2 rounded-xl text-xs leading-relaxed
                ${msg.role === "user"
                  ? "bg-blue-700 text-blue-100 rounded-br-sm"
                  : "bg-gray-800 text-gray-300 rounded-bl-sm"
                }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 px-3 py-2 rounded-xl text-xs text-gray-400">...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-gray-800">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ra lệnh hoặc hỏi Milo..."
            rows={2}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200
              placeholder-gray-500 outline-none focus:border-blue-500 resize-none"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="w-8 h-8 bg-blue-700 rounded-lg flex items-center justify-center flex-shrink-0
              hover:bg-blue-600 disabled:opacity-30 transition-all self-end"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-1.5">VD: "làm lại cảnh 2" · "đổi hashtag"</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/Stepper.tsx frontend/components/NavBar.tsx frontend/components/ChatSidebar.tsx
git commit -m "feat: shared UI components — Stepper, NavBar, ChatSidebar"
```

---

## Task 4: Sessions Page

**Files:**
- Create: `frontend/components/SessionCard.tsx`
- Create: `frontend/app/sessions/page.tsx`

- [ ] **Step 1: Create components/SessionCard.tsx**

```typescript
"use client";
import { useRouter } from "next/navigation";
import { deleteSession } from "@/lib/api";
import type { Session } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";
import { vi } from "date-fns/locale";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-700 text-gray-300",
  in_progress: "bg-blue-900 text-blue-300",
  scheduled: "bg-yellow-900 text-yellow-300",
  published: "bg-emerald-900 text-emerald-300",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Nháp",
  in_progress: `Đang làm`,
  scheduled: "Đã lên lịch",
  published: "Đã đăng",
};

interface SessionCardProps {
  session: Session;
  onDeleted: () => void;
}

export default function SessionCard({ session, onDeleted }: SessionCardProps) {
  const router = useRouter();

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Xoá session này?")) return;
    await deleteSession(session.id);
    onDeleted();
  }

  return (
    <div
      onClick={() => router.push(`/studio/${session.id}`)}
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 cursor-pointer
        hover:border-gray-600 hover:bg-gray-800 transition-all group"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-semibold text-gray-100 text-sm leading-tight">{session.title}</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${STATUS_STYLES[session.status]}`}>
          {STATUS_LABELS[session.status]}
        </span>
      </div>

      {session.topic && (
        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{session.topic}</p>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">Bước {session.step}/6</span>
          <div className="h-1 w-16 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full"
              style={{ width: `${(session.step / 6) * 100}%` }}
            />
          </div>
        </div>
        <button
          onClick={handleDelete}
          className="text-gray-700 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100 transition-all"
        >
          xoá
        </button>
      </div>

      <p className="text-xs text-gray-700 mt-2">
        {session.created_at
          ? formatDistanceToNow(new Date(session.created_at), { addSuffix: true, locale: vi })
          : ""}
      </p>
    </div>
  );
}
```

- [ ] **Step 2: Create app/sessions/page.tsx**

```typescript
"use client";
import { useState } from "react";
import useSWR from "swr";
import { useRouter } from "next/navigation";
import { listSessions, createSession } from "@/lib/api";
import SessionCard from "@/components/SessionCard";

export default function SessionsPage() {
  const router = useRouter();
  const { data: sessions, mutate } = useSWR("sessions", listSessions);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [lang, setLang] = useState("vi");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    const session = await createSession(title.trim(), lang);
    setTitle("");
    setCreating(false);
    mutate();
    router.push(`/studio/${session.id}`);
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-bold text-gray-100">🤖 Milo Studio</h1>
            <p className="text-sm text-gray-500 mt-0.5">Quản lý các video đang làm</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/schedule")}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-gray-800 text-gray-300 text-sm hover:bg-gray-700 transition-all"
            >
              📅 Lịch đăng
            </button>
            <button
              onClick={() => setCreating(true)}
              className="px-4 py-2 rounded-lg bg-blue-700 border border-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition-all"
            >
              + Video mới
            </button>
          </div>
        </div>

        {creating && (
          <form onSubmit={handleCreate} className="bg-gray-900 border border-gray-700 rounded-xl p-5 mb-6">
            <h2 className="text-sm font-semibold text-gray-200 mb-4">Tạo video mới</h2>
            <div className="flex gap-3">
              <input
                autoFocus
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Tên video (VD: Bí quyết ngủ ngon)"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200
                  placeholder-gray-500 outline-none focus:border-blue-500"
              />
              <select
                value={lang}
                onChange={(e) => setLang(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 outline-none"
              >
                <option value="vi">Tiếng Việt</option>
                <option value="en">English</option>
              </select>
              <button type="submit" className="px-4 py-2 rounded-lg bg-blue-700 text-white text-sm font-medium hover:bg-blue-600">
                Tạo
              </button>
              <button type="button" onClick={() => setCreating(false)} className="px-4 py-2 rounded-lg border border-gray-700 text-gray-400 text-sm hover:bg-gray-800">
                Huỷ
              </button>
            </div>
          </form>
        )}

        {!sessions ? (
          <p className="text-gray-600 text-sm">Đang tải...</p>
        ) : sessions.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-600 text-sm mb-4">Chưa có video nào.</p>
            <button onClick={() => setCreating(true)} className="px-4 py-2 bg-blue-700 rounded-lg text-white text-sm">
              Tạo video đầu tiên
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {sessions.map((s) => (
              <SessionCard key={s.id} session={s} onDeleted={() => mutate()} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Test in browser**

Start backend: `cd backend && uvicorn main:app --reload --port 8000`
Start frontend: `cd frontend && npm run dev`
Visit `http://localhost:3000/sessions`

Expected: sessions grid loads, "Video mới" button works, creating session redirects to studio page (404 for now).

- [ ] **Step 4: Commit**

```bash
git add frontend/components/SessionCard.tsx frontend/app/sessions/
git commit -m "feat: sessions page — grid view, create session, resume session"
```

---

## Task 5: Studio Wizard Page + Step 1

**Files:**
- Create: `frontend/app/studio/[sessionId]/page.tsx`
- Create: `frontend/components/steps/Step1Trend.tsx`

- [ ] **Step 1: Create app/studio/[sessionId]/page.tsx**

```typescript
"use client";
import { use, useState } from "react";
import useSWR from "swr";
import { getSession, updateSession } from "@/lib/api";
import Stepper from "@/components/Stepper";
import ChatSidebar from "@/components/ChatSidebar";
import Step1Trend from "@/components/steps/Step1Trend";
import Step2Scenes from "@/components/steps/Step2Scenes";
import Step3Images from "@/components/steps/Step3Images";
import Step4Video from "@/components/steps/Step4Video";
import Step5Merge from "@/components/steps/Step5Merge";
import Step6Publish from "@/components/steps/Step6Publish";

export default function StudioPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = use(params);
  const id = parseInt(sessionId);
  const { data: session, mutate } = useSWR(`session-${id}`, () => getSession(id));

  async function goToStep(n: number) {
    await updateSession(id, { step: n });
    mutate();
  }

  if (!session) return (
    <div className="h-screen bg-gray-950 flex items-center justify-center text-gray-600 text-sm">
      Đang tải session...
    </div>
  );

  const stepComponents: Record<number, React.ReactNode> = {
    1: <Step1Trend session={session} onAdvance={() => goToStep(2)} />,
    2: <Step2Scenes session={session} onAdvance={() => goToStep(3)} onBack={() => goToStep(1)} />,
    3: <Step3Images session={session} onAdvance={() => goToStep(4)} onBack={() => goToStep(2)} />,
    4: <Step4Video session={session} onAdvance={() => goToStep(5)} onBack={() => goToStep(3)} />,
    5: <Step5Merge session={session} onAdvance={() => goToStep(6)} onBack={() => goToStep(4)} />,
    6: <Step6Publish session={session} onBack={() => goToStep(5)} />,
  };

  return (
    <div className="h-screen flex flex-col bg-gray-950 overflow-hidden">
      <div className="flex-shrink-0">
        <div className="px-6 py-2 bg-gray-900 border-b border-gray-800 flex items-center gap-3">
          <a href="/sessions" className="text-xs text-gray-500 hover:text-gray-300">← Sessions</a>
          <span className="text-xs text-gray-700">/</span>
          <span className="text-xs text-gray-300 font-medium">{session.title}</span>
        </div>
        <Stepper currentStep={session.step} />
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-hidden flex flex-col">
          {stepComponents[session.step] ?? <div className="p-6 text-gray-500">Unknown step</div>}
        </div>
        <ChatSidebar sessionId={id} step={session.step} />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create components/steps/Step1Trend.tsx**

```typescript
"use client";
import { useState } from "react";
import { fetchTrends, generateScripts, updateSession } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session, TrendTopic } from "@/lib/types";

type SubStep = "trends" | "topic" | "scripts";

export default function Step1Trend({ session, onAdvance }: { session: Session; onAdvance: () => void }) {
  const [subStep, setSubStep] = useState<SubStep>("trends");
  const [trends, setTrends] = useState<TrendTopic[]>([]);
  const [topic, setTopic] = useState(session.topic ?? "");
  const [scripts, setScripts] = useState<string[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadTrends() {
    setLoading(true);
    try {
      const data = await fetchTrends(session.id);
      setTrends(data);
      setSubStep("trends");
    } finally {
      setLoading(false);
    }
  }

  async function confirmTopic() {
    await updateSession(session.id, { topic });
    setSubStep("scripts");
    setLoading(true);
    try {
      const data = await generateScripts(session.id);
      setScripts(data.scripts);
    } finally {
      setLoading(false);
    }
  }

  async function confirmScript() {
    if (selected === null) return;
    await updateSession(session.id, { topic, status: "in_progress" });
    onAdvance();
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 1 — Kịch bản</h2>

        {/* SUB-STEP NAV */}
        <div className="flex gap-3 mb-5">
          {(["trends", "topic", "scripts"] as SubStep[]).map((s, i) => (
            <div key={s} className={`flex items-center gap-2 text-xs ${subStep === s ? "text-blue-300 font-semibold" : "text-gray-600"}`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold
                ${subStep === s ? "bg-blue-700 text-white" : "bg-gray-800 text-gray-500"}`}>{i + 1}</span>
              {s === "trends" ? "Trend research" : s === "topic" ? "Chọn chủ đề" : "Chọn kịch bản"}
            </div>
          ))}
        </div>

        {/* 1A: TREND LIST */}
        {subStep === "trends" && (
          <div>
            <p className="text-sm text-gray-400 mb-4">Fetch trends đang hot về sức khoẻ + AI.</p>
            {trends.length === 0 ? (
              <button onClick={loadTrends} disabled={loading}
                className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50">
                {loading ? "Đang tìm..." : "🔍 Fetch trends"}
              </button>
            ) : (
              <div className="space-y-2">
                {trends.map((t, i) => (
                  <div key={i} onClick={() => { setTopic(t.topic); setSubStep("topic"); }}
                    className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 cursor-pointer hover:border-gray-600 transition-all">
                    <div>
                      <p className="text-sm text-gray-200">{t.topic}</p>
                      <p className="text-xs text-gray-500">{t.source}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-1 w-12 bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${t.score}%` }} />
                      </div>
                      <span className="text-xs text-gray-500">{t.score}</span>
                    </div>
                  </div>
                ))}
                <button onClick={() => setSubStep("topic")}
                  className="mt-3 px-4 py-2 border border-gray-700 rounded-lg text-sm text-gray-300 hover:bg-gray-800">
                  Tự nhập chủ đề →
                </button>
              </div>
            )}
          </div>
        )}

        {/* 1B: TOPIC CONFIRM */}
        {subStep === "topic" && (
          <div>
            <p className="text-sm text-gray-400 mb-4">Xác nhận hoặc chỉnh lại chủ đề trước khi tạo kịch bản.</p>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Nhập hoặc chỉnh chủ đề video..."
              rows={3}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm text-gray-200
                placeholder-gray-500 outline-none focus:border-blue-500 resize-none mb-4"
            />
            <button onClick={confirmTopic} disabled={!topic.trim() || loading}
              className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50">
              {loading ? "Đang tạo kịch bản..." : "✓ Xác nhận & tạo kịch bản"}
            </button>
          </div>
        )}

        {/* 1C: SCRIPT SELECT */}
        {subStep === "scripts" && (
          <div>
            <p className="text-sm text-gray-400 mb-4">Chọn 1 kịch bản để tiếp tục. Có thể chỉnh sửa trực tiếp.</p>
            <div className="space-y-3">
              {scripts.map((script, i) => (
                <div key={i} onClick={() => setSelected(i)}
                  className={`bg-gray-900 border rounded-xl p-4 cursor-pointer transition-all
                    ${selected === i ? "border-blue-500" : "border-gray-800 hover:border-gray-600"}`}>
                  <div className="text-xs text-gray-500 font-semibold mb-2">Kịch bản {i + 1}</div>
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{script}</pre>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <NavBar
        step={1} totalSteps={6}
        onBack={() => {}}
        onNext={subStep === "trends" && trends.length > 0 ? () => setSubStep("topic")
          : subStep === "topic" ? confirmTopic
          : confirmScript}
        nextDisabled={
          (subStep === "trends" && trends.length === 0) ||
          (subStep === "topic" && !topic.trim()) ||
          (subStep === "scripts" && selected === null) ||
          loading
        }
        nextLabel={subStep === "scripts" ? "OK, qua Bước 2 →" : "Tiếp →"}
      />
    </div>
  );
}
```

- [ ] **Step 3: Create stub components for steps 2–6 (so studio page compiles)**

Create `frontend/components/steps/Step2Scenes.tsx`:
```typescript
export default function Step2Scenes({ session, onAdvance, onBack }: any) {
  return <div className="p-6 text-gray-400 text-sm">Step 2 — Phân cảnh (coming soon)<br/>
    <button onClick={onAdvance} className="mt-4 px-4 py-2 bg-blue-700 rounded text-white text-xs">Next →</button>
    <button onClick={onBack} className="mt-4 ml-2 px-4 py-2 bg-gray-700 rounded text-white text-xs">← Back</button>
  </div>;
}
```

Repeat same stub pattern for `Step3Images.tsx`, `Step4Video.tsx`, `Step5Merge.tsx`, `Step6Publish.tsx` — same props `{ session, onAdvance, onBack }`.

- [ ] **Step 4: Test in browser**

Visit `http://localhost:3000/sessions` → create session → verify wizard opens at Step 1 with stepper, chatbox, and trend fetch button.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/studio/ frontend/components/steps/
git commit -m "feat: studio wizard page + Step 1 (trend research, topic confirm, script select)"
```

---

## Task 6: Step 2 — Scene Breakdown

**Files:**
- Modify: `frontend/components/steps/Step2Scenes.tsx`

- [ ] **Step 1: Implement Step2Scenes.tsx**

```typescript
"use client";
import { useState } from "react";
import useSWR from "swr";
import { splitScenes } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session, Scene } from "@/lib/types";

export default function Step2Scenes({
  session, onAdvance, onBack,
}: { session: Session; onAdvance: () => void; onBack: () => void }) {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(false);
  const [scriptInput, setScriptInput] = useState("");
  const [generated, setGenerated] = useState(false);

  async function handleGenerate() {
    if (!scriptInput.trim()) return;
    setLoading(true);
    try {
      const data = await splitScenes(session.id, scriptInput);
      setScenes(data.scenes);
      setGenerated(true);
    } finally {
      setLoading(false);
    }
  }

  function updateScene(id: number, text: string) {
    setScenes((prev) => prev.map((s) => s.id === id ? { ...s, script_text: text } : s));
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 2 — Phân cảnh</h2>
        <p className="text-sm text-gray-500 mb-5">Paste kịch bản đã chọn để phân thành các cảnh.</p>

        {!generated ? (
          <div>
            <textarea
              value={scriptInput}
              onChange={(e) => setScriptInput(e.target.value)}
              placeholder="Paste kịch bản vào đây..."
              rows={8}
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-200
                placeholder-gray-500 outline-none focus:border-blue-500 resize-none mb-4"
            />
            <button onClick={handleGenerate} disabled={!scriptInput.trim() || loading}
              className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50">
              {loading ? "Đang phân cảnh..." : "🎬 Phân cảnh tự động"}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {scenes.map((scene, i) => (
              <div key={scene.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-500">CẢNH {i + 1}</span>
                  <span className="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full">{scene.emotion_tag}</span>
                </div>
                <textarea
                  value={scene.script_text}
                  onChange={(e) => updateScene(scene.id, e.target.value)}
                  rows={3}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200
                    outline-none focus:border-blue-500 resize-none"
                />
              </div>
            ))}
          </div>
        )}
      </div>
      <NavBar
        step={2} totalSteps={6}
        onBack={onBack}
        onNext={onAdvance}
        nextDisabled={scenes.length === 0}
      />
    </div>
  );
}
```

- [ ] **Step 2: Test in browser — verify scenes appear and are editable**

- [ ] **Step 3: Commit**

```bash
git add frontend/components/steps/Step2Scenes.tsx
git commit -m "feat: Step 2 — scene breakdown with editable scene list"
```

---

## Task 7: Step 3 — Image Selection

**Files:**
- Modify: `frontend/components/steps/Step3Images.tsx`

- [ ] **Step 1: Implement Step3Images.tsx**

```typescript
"use client";
import { useState } from "react";
import useSWR from "swr";
import { assignImages, listMiloImages } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session, Scene, MiloImage } from "@/lib/types";

export default function Step3Images({
  session, onAdvance, onBack,
}: { session: Session; onAdvance: () => void; onBack: () => void }) {
  const { data: scenes = [], mutate: mutateScenes } = useSWR(`scenes-${session.id}`, () => getScenes(session.id));
  const [loading, setLoading] = useState(false);
  const [approvedIds, setApprovedIds] = useState<Set<number>>(new Set());
  const [swappingId, setSwappingId] = useState<number | null>(null);
  const { data: allImages } = useSWR("milo-images", () => listMiloImages());

  async function handleAutoAssign() {
    setLoading(true);
    try {
      const data = await assignImages(session.id);
      setScenes(data.scenes);
    } finally {
      setLoading(false);
    }
  }

  function toggleApprove(id: number) {
    setApprovedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function swapImage(sceneId: number, imgPath: string) {
    setScenes((prev) => prev.map((s) => s.id === sceneId ? { ...s, image_path: imgPath } : s));
    setSwappingId(null);
  }

  const imgFilename = (path: string | null) => path?.split("/").pop() ?? "";

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 3 — Chọn ảnh Milo</h2>
        <p className="text-sm text-gray-500 mb-5">AI chọn ảnh phù hợp từ thư viện. Review và approve từng cảnh.</p>

        {scenes.length === 0 ? (
          <button onClick={handleAutoAssign} disabled={loading}
            className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50">
            {loading ? "Đang chọn ảnh..." : "🖼 Auto-assign ảnh Milo"}
          </button>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {scenes.map((scene, i) => (
              <div key={scene.id}
                className={`bg-gray-900 border rounded-xl overflow-hidden transition-all
                  ${approvedIds.has(scene.id) ? "border-emerald-600" : "border-gray-800"}`}>
                <div className="bg-gradient-to-br from-blue-950 to-purple-950 h-32 flex items-center justify-center text-4xl">
                  🤖
                </div>
                <div className="p-3">
                  <div className="text-xs text-gray-500 font-semibold mb-1">CẢNH {i + 1} · {scene.emotion_tag}</div>
                  <p className="text-xs text-gray-400 mb-2 line-clamp-2">{scene.script_text}</p>
                  <p className="text-xs text-gray-600 mb-3">{imgFilename(scene.image_path)}</p>
                  <div className="flex gap-2">
                    <button onClick={() => toggleApprove(scene.id)}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all
                        ${approvedIds.has(scene.id) ? "bg-emerald-900 text-emerald-300" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}>
                      {approvedIds.has(scene.id) ? "✓ OK" : "Approve"}
                    </button>
                    <button onClick={() => setSwappingId(swappingId === scene.id ? null : scene.id)}
                      className="flex-1 py-1.5 rounded-lg text-xs bg-gray-800 text-gray-400 hover:bg-gray-700">
                      ↻ Đổi ảnh
                    </button>
                  </div>
                  {swappingId === scene.id && allImages && (
                    <div className="mt-3 grid grid-cols-3 gap-1">
                      {allImages.map((img) => (
                        <button key={img.filename} onClick={() => swapImage(scene.id, img.path)}
                          className="bg-gray-800 rounded p-1 text-xs text-gray-400 hover:bg-gray-700 truncate">
                          {img.filename.replace("milo_", "").replace(".png", "")}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <NavBar
        step={3} totalSteps={6}
        approvedCount={approvedIds.size}
        totalCount={scenes.length}
        onBack={onBack}
        onNext={onAdvance}
        nextDisabled={approvedIds.size < scenes.length || scenes.length === 0}
      />
    </div>
  );
}
```

- [ ] **Step 2: Test in browser — verify auto-assign + approve + swap flow**

- [ ] **Step 3: Commit**

```bash
git add frontend/components/steps/Step3Images.tsx
git commit -m "feat: Step 3 — Milo image selection with approve/swap per scene"
```

---

## Task 8: Steps 4, 5, 6

**Files:**
- Modify: `frontend/components/steps/Step4Video.tsx`
- Modify: `frontend/components/steps/Step5Merge.tsx`
- Modify: `frontend/components/steps/Step6Publish.tsx`

- [ ] **Step 1: Implement Step4Video.tsx**

```typescript
"use client";
import { useState } from "react";
import { genSceneVideo } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session, Scene } from "@/lib/types";

export default function Step4Video({
  session, onAdvance, onBack,
}: { session: Session; onAdvance: () => void; onBack: () => void }) {
  const { data: scenes = [] } = useSWR(`scenes-${session.id}`, () => getScenes(session.id));
  const [generating, setGenerating] = useState<Record<number, boolean>>({});
  const [done, setDone] = useState<Set<number>>(new Set());

  async function genVideo(scene: Scene) {
    setGenerating((prev) => ({ ...prev, [scene.id]: true }));
    try {
      await genSceneVideo(session.id, scene.id);
      setDone((prev) => new Set(prev).add(scene.id));
    } finally {
      setGenerating((prev) => ({ ...prev, [scene.id]: false }));
    }
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 4 — Tạo video từng cảnh</h2>
        <p className="text-sm text-gray-500 mb-5">TTS + ken-burns effect cho từng cảnh. Preview trước khi tiếp.</p>
        {scenes.length === 0 && (
          <p className="text-sm text-gray-600">Quay lại bước 3 để assign ảnh trước.</p>
        )}
        <div className="space-y-3">
          {scenes.map((scene, i) => (
            <div key={scene.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
              <div className="flex-1">
                <div className="text-xs text-gray-500 mb-1">CẢNH {i + 1}</div>
                <p className="text-xs text-gray-300 line-clamp-2">{scene.script_text}</p>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                {done.has(scene.id) && (
                  <span className="text-xs text-emerald-400 px-2 py-1 bg-emerald-900/40 rounded-lg">✓ Done</span>
                )}
                <button onClick={() => genVideo(scene)} disabled={generating[scene.id]}
                  className="px-3 py-1.5 bg-blue-700 rounded-lg text-xs text-white disabled:opacity-50 hover:bg-blue-600">
                  {generating[scene.id] ? "Đang gen..." : done.has(scene.id) ? "↻ Redo" : "▶ Gen"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      <NavBar step={4} totalSteps={6} onBack={onBack} onNext={onAdvance}
        nextDisabled={scenes.length > 0 && done.size < scenes.length} />
    </div>
  );
}
```

- [ ] **Step 2: Implement Step5Merge.tsx**

```typescript
"use client";
import { useState } from "react";
import { mergeVideo } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session } from "@/lib/types";

export default function Step5Merge({
  session, onAdvance, onBack,
}: { session: Session; onAdvance: () => void; onBack: () => void }) {
  const [bgmVolume, setBgmVolume] = useState(0.15);
  const [caption, setCaption] = useState("");
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [videoPath, setVideoPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleMerge() {
    setLoading(true);
    try {
      const data = await mergeVideo(session.id, "", bgmVolume);
      setVideoPath(data.final_video_path);
      setCaption(data.caption);
      setHashtags(data.hashtags);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 5 — Ghép video + Caption</h2>
        <p className="text-sm text-gray-500 mb-5">Ghép tất cả cảnh, thêm nhạc nền và tạo caption.</p>

        <div className="mb-5">
          <label className="text-xs text-gray-400 block mb-2">Âm lượng nhạc nền: {Math.round(bgmVolume * 100)}%</label>
          <input type="range" min={0} max={0.5} step={0.05} value={bgmVolume}
            onChange={(e) => setBgmVolume(parseFloat(e.target.value))}
            className="w-48 accent-blue-500" />
        </div>

        <button onClick={handleMerge} disabled={loading}
          className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50 mb-6">
          {loading ? "Đang ghép..." : "✂️ Ghép video"}
        </button>

        {videoPath && (
          <div className="space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="text-xs text-gray-500 mb-2 font-semibold">FINAL VIDEO</div>
              <p className="text-xs text-green-400">{videoPath}</p>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-2">Caption</label>
              <textarea value={caption} onChange={(e) => setCaption(e.target.value)} rows={3}
                className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-200
                  outline-none focus:border-blue-500 resize-none" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-2">Hashtags</label>
              <div className="flex flex-wrap gap-1.5">
                {hashtags.map((tag, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 bg-gray-800 text-blue-300 rounded-full">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
      <NavBar step={5} totalSteps={6} onBack={onBack} onNext={onAdvance} nextDisabled={!videoPath} />
    </div>
  );
}
```

- [ ] **Step 3: Implement Step6Publish.tsx**

```typescript
"use client";
import { useState } from "react";
import { createSchedule, updateSession } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session } from "@/lib/types";

export default function Step6Publish({
  session, onBack,
}: { session: Session; onBack: () => void }) {
  const [postTime, setPostTime] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [done, setDone] = useState(false);

  async function handlePublish() {
    if (!postTime) return;
    setPublishing(true);
    try {
      await createSchedule({ session_id: session.id, post_time: new Date(postTime).toISOString() });
      await updateSession(session.id, { status: "scheduled" });
      setDone(true);
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 6 — Xuất & Lên lịch đăng</h2>
        <p className="text-sm text-gray-500 mb-6">Chọn thời điểm đăng lên TikTok.</p>

        {done ? (
          <div className="bg-emerald-900/30 border border-emerald-700 rounded-xl p-6 text-center">
            <div className="text-3xl mb-3">🎉</div>
            <p className="text-emerald-300 font-semibold">Video đã được lên lịch đăng!</p>
            <p className="text-xs text-emerald-500 mt-1">{new Date(postTime).toLocaleString("vi-VN")}</p>
            <a href="/sessions" className="mt-4 inline-block text-sm text-blue-300 hover:underline">← Về trang chính</a>
          </div>
        ) : (
          <div>
            <label className="text-xs text-gray-400 block mb-2">Ngày & giờ đăng</label>
            <input type="datetime-local" value={postTime} onChange={(e) => setPostTime(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200
                outline-none focus:border-blue-500 mb-6" />
            <button onClick={handlePublish} disabled={!postTime || publishing}
              className="block px-6 py-2.5 bg-emerald-700 rounded-lg text-sm text-white font-semibold
                disabled:opacity-50 hover:bg-emerald-600 transition-all">
              {publishing ? "Đang lên lịch..." : "🚀 Lên lịch đăng TikTok"}
            </button>
          </div>
        )}
      </div>
      <NavBar step={6} totalSteps={6} onBack={onBack} onNext={() => {}} nextDisabled={true} nextLabel="Hoàn thành" />
    </div>
  );
}
```

- [ ] **Step 4: Test full wizard flow in browser**

```
/sessions → create session → step 1 (fetch trends) → step 2 → ... → step 6 → verify session status = "scheduled" in /sessions
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/steps/
git commit -m "feat: Steps 4-6 — scene video gen, video merge+caption, schedule+publish"
```

---

## Task 9: Schedule Page

**Files:**
- Create: `frontend/components/ScheduleCalendar.tsx`
- Create: `frontend/app/schedule/page.tsx`

- [ ] **Step 1: Create components/ScheduleCalendar.tsx**

```typescript
"use client";
import useSWR from "swr";
import { listSchedule, updateSchedule } from "@/lib/api";
import { format, parseISO } from "date-fns";
import { vi } from "date-fns/locale";

export default function ScheduleCalendar() {
  const { data: entries, mutate } = useSWR("schedule", listSchedule);

  const STATUS_STYLE: Record<string, string> = {
    pending: "bg-yellow-900 text-yellow-300",
    scheduled: "bg-blue-900 text-blue-300",
    published: "bg-emerald-900 text-emerald-300",
    failed: "bg-red-900 text-red-300",
  };

  if (!entries) return <p className="text-gray-600 text-sm p-6">Đang tải...</p>;
  if (entries.length === 0) return <p className="text-gray-600 text-sm p-6">Chưa có video nào được lên lịch.</p>;

  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div key={entry.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-200 mb-1">
                📅 {format(parseISO(entry.post_time), "EEEE, dd/MM/yyyy HH:mm", { locale: vi })}
              </div>
              {entry.caption && (
                <p className="text-xs text-gray-500 line-clamp-2">{entry.caption}</p>
              )}
              {entry.hashtags && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {JSON.parse(entry.hashtags ?? "[]").slice(0, 5).map((tag: string, i: number) => (
                    <span key={i} className="text-xs px-2 py-0.5 bg-gray-800 text-blue-400 rounded-full">{tag}</span>
                  ))}
                </div>
              )}
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${STATUS_STYLE[entry.status] ?? ""}`}>
              {entry.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create app/schedule/page.tsx**

```typescript
"use client";
import ScheduleCalendar from "@/components/ScheduleCalendar";
import { useRouter } from "next/navigation";

export default function SchedulePage() {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-bold text-gray-100">📅 Lịch đăng</h1>
            <p className="text-sm text-gray-500 mt-0.5">Các video đã lên lịch và đã đăng</p>
          </div>
          <button onClick={() => router.push("/sessions")}
            className="px-4 py-2 rounded-lg border border-gray-700 bg-gray-800 text-gray-300 text-sm hover:bg-gray-700">
            ← Sessions
          </button>
        </div>
        <ScheduleCalendar />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Test in browser**

Visit `http://localhost:3000/schedule` — verify scheduled videos appear with correct date/time format.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/ScheduleCalendar.tsx frontend/app/schedule/
git commit -m "feat: schedule page — list scheduled and published videos"
```

---

## Task 10: Final Verification

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: all tests PASS.

- [ ] **Step 2: End-to-end smoke test**

```
1. Start backend: uvicorn main:app --reload --port 8000
2. Start frontend: npm run dev
3. Visit http://localhost:3000
4. Create new session "Test ngủ ngon"
5. Step 1: fetch trends → pick topic → gen scripts → select one → next
6. Step 2: paste script → split scenes → verify 3-5 scenes → next
7. Step 3: auto-assign images → approve all → next
8. Step 4: gen video for scene 1 → verify no FFmpeg error → next
9. Step 5: merge → verify caption generated → next
10. Step 6: set post time → publish → verify status = "scheduled"
11. Visit /schedule → verify entry appears
12. Visit /sessions → verify session shows "Đã lên lịch"
```

- [ ] **Step 3: Build check**

```bash
cd frontend
npm run build
```

Expected: build completes with no errors.

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: Milo Studio v1.0 — full pipeline frontend complete"
```
