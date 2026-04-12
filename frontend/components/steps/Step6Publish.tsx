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
