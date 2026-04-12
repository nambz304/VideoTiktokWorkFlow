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
