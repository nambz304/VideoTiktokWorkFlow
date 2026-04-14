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
            <h1 className="text-xl font-bold text-gray-100">🤖 Tiktok Studio</h1>
            <p className="text-sm text-gray-500 mt-0.5">Quản lý các video đang làm</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/characters")}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-gray-800 text-gray-300 text-sm hover:bg-gray-700 transition-all"
            >
              🎭 Nhân vật
            </button>
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
