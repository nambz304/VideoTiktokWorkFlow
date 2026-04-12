"use client";
import { useState } from "react";
import useSWR from "swr";
import { genSceneVideo, getScenes } from "@/lib/api";
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
