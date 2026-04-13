"use client";
import { useState } from "react";
import { splitScenes } from "@/lib/api";
import NavBar from "@/components/NavBar";
import CharacterManager from "@/components/CharacterManager";
import type { Session, Scene, Character } from "@/lib/types";

export default function Step2Scenes({
  session, onAdvance, onBack,
}: { session: Session; onAdvance: () => void; onBack: () => void }) {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(false);
  const [scriptInput, setScriptInput] = useState("");
  const [generated, setGenerated] = useState(false);
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);

  async function handleGenerate() {
    if (!scriptInput.trim()) return;
    setLoading(true);
    try {
      const data = await splitScenes(session.id, scriptInput, selectedCharacter?.id);
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

        <div className="mb-6">
          <CharacterManager
            selectedId={selectedCharacter?.id ?? null}
            onSelect={setSelectedCharacter}
          />
        </div>

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
