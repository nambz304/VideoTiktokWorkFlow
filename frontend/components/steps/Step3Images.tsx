"use client";
import { useState } from "react";
import useSWR from "swr";
import { assignImages, listMiloImages, getScenes } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session, Scene, MiloImage } from "@/lib/types";

export default function Step3Images({
  session, onAdvance, onBack,
}: { session: Session; onAdvance: () => void; onBack: () => void }) {
  const { data: swrScenes = [] } = useSWR(`scenes-${session.id}`, () => getScenes(session.id));
  const [localScenes, setLocalScenes] = useState<Scene[] | null>(null);
  const scenes = localScenes ?? swrScenes;

  const [loading, setLoading] = useState(false);
  const [approvedIds, setApprovedIds] = useState<Set<number>>(new Set());
  const [swappingId, setSwappingId] = useState<number | null>(null);
  const { data: allImages } = useSWR("milo-images", () => listMiloImages());

  async function handleAutoAssign() {
    setLoading(true);
    try {
      const data = await assignImages(session.id);
      setLocalScenes(data.scenes);
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
    setLocalScenes((prev) => (prev ?? swrScenes).map((s) => s.id === sceneId ? { ...s, image_path: imgPath } : s));
    setSwappingId(null);
  }

  const imgFilename = (path: string | null) => path?.split("/").pop() ?? "";
  const imageUrl = (path: string | null) => path ? `/static/milo/${path.split("/").pop()}` : "";

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 3 — Chọn ảnh Milo</h2>
        <p className="text-sm text-gray-500 mb-5">AI chọn ảnh phù hợp từ thư viện. Review và approve từng cảnh.</p>

        {scenes.length === 0 || !scenes.some((s) => s.image_path) ? (
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
                <img src={imageUrl(scene.image_path)} alt={imgFilename(scene.image_path)}
                  className="h-32 w-full object-contain bg-gray-900" />
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
                          className="bg-gray-800 rounded p-1 text-xs text-gray-400 hover:bg-gray-700 flex flex-col items-center gap-1">
                          <img src={img.url} alt={img.filename} className="h-10 w-10 object-contain" />
                          <span className="truncate w-full text-center">{img.filename.replace("milo_", "").replace(".png", "")}</span>
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
