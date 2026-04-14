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
  const [merged, setMerged] = useState(false);
  const [loading, setLoading] = useState(false);
  const [videoKey, setVideoKey] = useState(0); // force re-render video after re-merge

  async function handleMerge() {
    setLoading(true);
    try {
      const data = await mergeVideo(session.id, "", bgmVolume);
      setCaption(data.caption);
      setHashtags(data.hashtags);
      setMerged(true);
      setVideoKey((k) => k + 1);
    } finally {
      setLoading(false);
    }
  }

  const videoSrc = `/api/sessions/${session.id}/video`;

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 5 — Ghép video + Caption</h2>
        <p className="text-sm text-gray-500 mb-5">Ghép tất cả cảnh, thêm nhạc nền và tạo caption.</p>

        {/* Video frame — luôn hiển thị */}
        <div className="mb-5 bg-black rounded-xl overflow-hidden flex items-center justify-center"
             style={{ aspectRatio: "9/16", maxHeight: 400, width: "fit-content", minWidth: 180, margin: "0 auto 20px" }}>
          {merged ? (
            <video
              key={videoKey}
              src={videoSrc}
              controls
              autoPlay={false}
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="flex flex-col items-center gap-3 text-center px-6">
              {loading ? (
                <>
                  <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-xs text-gray-400">Đang ghép video...</span>
                </>
              ) : (
                <>
                  <span className="text-3xl">🎬</span>
                  <span className="text-xs text-gray-500">Bấm "Ghép video" để xem kết quả</span>
                </>
              )}
            </div>
          )}
        </div>

        {/* Download button — hiện sau khi đã merge */}
        {merged && (
          <a
            href={videoSrc}
            download={`milo_session_${session.id}.mp4`}
            className="flex items-center justify-center gap-2 text-sm bg-emerald-700 hover:bg-emerald-600 px-4 py-2 rounded-lg text-white font-semibold transition-colors mb-5"
          >
            ⬇ Tải video về máy
          </a>
        )}

        {/* Controls */}
        <div className="mb-4">
          <label className="text-xs text-gray-400 block mb-2">Âm lượng nhạc nền: {Math.round(bgmVolume * 100)}%</label>
          <input type="range" min={0} max={0.5} step={0.05} value={bgmVolume}
            onChange={(e) => setBgmVolume(parseFloat(e.target.value))}
            className="w-48 accent-blue-500" />
        </div>

        <button onClick={handleMerge} disabled={loading}
          className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50 hover:bg-blue-600 transition-colors mb-6">
          {loading ? "Đang ghép..." : merged ? "↻ Ghép lại" : "✂️ Ghép video"}
        </button>

        {/* Caption & hashtags */}
        {merged && (
          <div className="space-y-4">
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
      <NavBar step={5} totalSteps={6} onBack={onBack} onNext={onAdvance} nextDisabled={false} />
    </div>
  );
}
