"use client";
import { useState } from "react";
import useSWR from "swr";
import { genSceneImage, getScenes } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session, Scene } from "@/lib/types";

export default function Step3Images({
  session, onAdvance, onBack,
}: { session: Session; onAdvance: () => void; onBack: () => void }) {
  const { data: swrScenes = [], mutate } = useSWR(`scenes-${session.id}`, () => getScenes(session.id));
  const [generating, setGenerating] = useState<Record<number, boolean>>({});
  const [errors, setErrors] = useState<Record<number, string>>({});

  function imageUrl(path: string | null) {
    if (!path) return null;
    const filename = path.split("/").pop();
    return `/output/images/${filename}`;
  }

  async function handleGen(scene: Scene) {
    setGenerating((prev) => ({ ...prev, [scene.id]: true }));
    setErrors((prev) => { const n = { ...prev }; delete n[scene.id]; return n; });
    try {
      await genSceneImage(session.id, scene.id);
      await mutate();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Lỗi không xác định";
      setErrors((prev) => ({ ...prev, [scene.id]: msg }));
    } finally {
      setGenerating((prev) => ({ ...prev, [scene.id]: false }));
    }
  }

  const allHaveImages = swrScenes.length > 0 && swrScenes.every((s) => s.image_path);

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 3 — Gen ảnh cảnh</h2>
        <p className="text-sm text-gray-400 mb-5">
          Gen ảnh từng cảnh bằng FLUX Kontext. Đọc text và xem ảnh — nếu chưa khớp, gen lại.
        </p>

        {swrScenes.length === 0 ? (
          <p className="text-xs text-gray-600 text-center py-10">Chưa có cảnh nào.</p>
        ) : (
          <div className="space-y-4">
            {swrScenes.map((scene, i) => {
              const isGen = generating[scene.id];
              const err = errors[scene.id];
              const imgUrl = imageUrl(scene.image_path);

              return (
                <div key={scene.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                  <div className="flex gap-4 p-4">
                    {/* Image area */}
                    <div className="flex-shrink-0 w-28 h-48 bg-gray-800 rounded-lg overflow-hidden flex items-center justify-center">
                      {isGen ? (
                        <div className="flex flex-col items-center gap-2">
                          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                          <span className="text-xs text-gray-500">Đang gen...</span>
                        </div>
                      ) : imgUrl ? (
                        <img src={imgUrl} alt={`scene ${i + 1}`} className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-xs text-gray-600 text-center px-2">Chưa có ảnh</span>
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

                      <div className="mt-3 flex flex-col gap-2">
                        {err && (
                          <p className="text-xs text-red-400 break-words">{err}</p>
                        )}
                        <button
                          onClick={() => handleGen(scene)}
                          disabled={isGen}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all disabled:opacity-40
                            ${scene.image_path
                              ? "bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700"
                              : "bg-blue-700 text-white hover:bg-blue-600"
                            }`}
                        >
                          {isGen ? "Đang gen..." : scene.image_path ? "↻ Gen lại" : "✨ Gen ảnh"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <NavBar
        step={3}
        totalSteps={6}
        onBack={onBack}
        onNext={onAdvance}
        nextDisabled={false}
        nextLabel={allHaveImages ? "Tiếp tục →" : swrScenes.length === 0 ? "Tiếp tục →" : `Bỏ qua (còn ${swrScenes.filter(s => !s.image_path).length} ảnh chưa gen)`}
      />
    </div>
  );
}
