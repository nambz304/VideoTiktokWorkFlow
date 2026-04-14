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
  const [videoPaths, setVideoPaths] = useState<Record<number, string>>({});
  const [errors, setErrors] = useState<Record<number, string>>({});

  function videoUrl(sceneId: number) {
    const path = videoPaths[sceneId];
    if (!path) return null;
    const filename = path.split("/").pop();
    return `/output/scenes/${filename}`;
  }

  async function genVideo(scene: Scene) {
    setGenerating((prev) => ({ ...prev, [scene.id]: true }));
    setErrors((prev) => { const n = { ...prev }; delete n[scene.id]; return n; });
    try {
      const data = await genSceneVideo(session.id, scene.id);
      setVideoPaths((prev) => ({ ...prev, [scene.id]: data.video_path }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Lỗi không xác định";
      setErrors((prev) => ({ ...prev, [scene.id]: msg }));
    } finally {
      setGenerating((prev) => ({ ...prev, [scene.id]: false }));
    }
  }

  const allDone = scenes.length > 0 && scenes.every((s) => videoPaths[s.id]);

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 4 — Tạo video từng cảnh</h2>
        <p className="text-sm text-gray-400 mb-5">
          Gen TTS + ghép ảnh cho từng cảnh. Xem preview — nếu chưa vừa ý, gen lại.
        </p>

        {scenes.length === 0 && (
          <p className="text-sm text-gray-600">Quay lại bước 3 để gen ảnh trước.</p>
        )}

        <div className="space-y-4">
          {scenes.map((scene, i) => {
            const isGen = generating[scene.id];
            const url = videoUrl(scene.id);
            const err = errors[scene.id];
            const hasVideo = !!url;

            return (
              <div key={scene.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                <div className="flex gap-4 p-4">
                  {/* Video frame — 9:16 ratio, cố định width */}
                  <div className="flex-shrink-0 w-36 bg-black rounded-lg overflow-hidden flex items-center justify-center"
                       style={{ aspectRatio: "9/16", minHeight: 200 }}>
                    {isGen ? (
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        <span className="text-xs text-gray-400">Đang gen...</span>
                      </div>
                    ) : url ? (
                      <video
                        key={url}
                        src={url}
                        controls
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="flex flex-col items-center gap-2 px-3 text-center">
                        <span className="text-2xl">🎬</span>
                        <span className="text-xs text-gray-600">Chưa có video</span>
                      </div>
                    )}
                  </div>

                  {/* Text + actions */}
                  <div className="flex-1 flex flex-col justify-between min-w-0">
                    <div>
                      <div className="text-xs text-gray-500 font-semibold mb-1">
                        CẢNH {i + 1} · {scene.emotion_tag?.toUpperCase()}
                      </div>
                      <p className="text-sm text-gray-200 leading-relaxed">{scene.script_text}</p>
                    </div>

                    <div className="mt-4 flex flex-col gap-2">
                      {err && <p className="text-xs text-red-400 break-words">{err}</p>}
                      {hasVideo && !isGen && (
                        <span className="text-xs text-emerald-400">✓ Đã gen xong</span>
                      )}
                      <button
                        onClick={() => genVideo(scene)}
                        disabled={isGen}
                        className={`px-3 py-2 rounded-lg text-xs font-semibold transition-all disabled:opacity-40
                          ${hasVideo
                            ? "bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700"
                            : "bg-blue-700 text-white hover:bg-blue-600"
                          }`}
                      >
                        {isGen ? "Đang gen..." : hasVideo ? "↻ Gen lại" : "▶ Gen video"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <NavBar
        step={4}
        totalSteps={6}
        onBack={onBack}
        onNext={onAdvance}
        nextDisabled={false}
        nextLabel={allDone ? "Tiếp tục →" : scenes.length === 0 ? "Tiếp tục →" : `Bỏ qua (còn ${scenes.filter(s => !videoPaths[s.id]).length} video chưa gen)`}
      />
    </div>
  );
}
