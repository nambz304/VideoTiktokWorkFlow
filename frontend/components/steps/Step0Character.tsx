"use client";
import { useState, useEffect, useRef } from "react";
import { listCharacters } from "@/lib/api";
import type { Character, Session } from "@/lib/types";

type Props = {
  session: Session;
  onAdvance: (characterId?: number) => void;
};

export default function Step0Character({ session, onAdvance }: Props) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selected, setSelected] = useState<number | null>(session.character_id ?? null);
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [personality, setPersonality] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    listCharacters().then((d) => setCharacters(d.characters));
  }, []);

  async function createCharacter() {
    if (!name.trim()) return;
    setLoading(true);
    const form = new FormData();
    form.append("name", name);
    form.append("personality", personality);
    files.forEach((f) => form.append("files", f));
    const res = await fetch(`${API}/characters/`, { method: "POST", body: form });
    const char: Character = await res.json();
    setCharacters((prev) => [char, ...prev]);
    setSelected(char.id);
    setCreating(false);
    setName("");
    setPersonality("");
    setFiles([]);
    setLoading(false);
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 0 — Chọn nhân vật</h2>
        <p className="text-sm text-gray-400 mb-5">
          Chọn nhân vật AI sẽ xuất hiện trong video (dùng Kontext), hoặc bỏ qua để dùng ảnh sprite mặc định.
        </p>

        <div className="space-y-2 mb-4">
          {characters.map((char) => (
            <div
              key={char.id}
              onClick={() => setSelected(char.id === selected ? null : char.id)}
              className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                ${selected === char.id
                  ? "border-blue-500 bg-blue-900/20"
                  : "border-gray-800 bg-gray-900 hover:border-gray-600"}`}
            >
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-base flex-shrink-0">
                🤖
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-200 truncate">{char.name}</div>
                <div className="text-xs text-gray-500">
                  {char.ref_image_count} ảnh ref
                  {char.fal_ready ? " · ✓ sẵn sàng" : " · ⏳ chưa upload fal"}
                </div>
              </div>
              {selected === char.id && (
                <span className="text-xs text-blue-400 font-semibold flex-shrink-0">✓ Đã chọn</span>
              )}
            </div>
          ))}

          {characters.length === 0 && !creating && (
            <p className="text-xs text-gray-600 text-center py-6">
              Chưa có nhân vật nào.
            </p>
          )}
        </div>

        {!creating && (
          <button
            onClick={() => setCreating(true)}
            className="text-xs border border-dashed border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-500 px-4 py-2 rounded-lg w-full"
          >
            + Tạo nhân vật mới
          </button>
        )}

        {creating && (
          <div className="border border-blue-500/30 bg-blue-900/10 rounded-lg p-4 space-y-3 mt-2">
            <div className="text-xs font-semibold text-blue-300">Tạo nhân vật mới</div>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Tên nhân vật (vd: Milo)"
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-blue-500"
            />
            <textarea
              value={personality}
              onChange={(e) => setPersonality(e.target.value)}
              placeholder="Mô tả tính cách: Robot vui vẻ, hài hước..."
              rows={2}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-blue-500 resize-none"
            />
            <div>
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(e) => setFiles(Array.from(e.target.files || []).slice(0, 3))}
              />
              <button
                onClick={() => fileRef.current?.click()}
                className="w-full border border-dashed border-gray-600 rounded py-3 text-xs text-gray-500 hover:border-gray-400 hover:text-gray-400"
              >
                {files.length > 0 ? `✓ ${files.length} ảnh đã chọn` : "📸 Upload 1-3 ảnh reference (tuỳ chọn)"}
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={createCharacter}
                disabled={loading || !name.trim()}
                className="flex-1 bg-blue-700 hover:bg-blue-600 disabled:opacity-40 py-2 rounded text-sm font-semibold text-white"
              >
                {loading ? "Đang tạo..." : "Tạo nhân vật"}
              </button>
              <button
                onClick={() => setCreating(false)}
                className="px-4 py-2 rounded text-sm text-gray-400 hover:text-gray-200 border border-gray-700"
              >
                Huỷ
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 px-6 py-3 bg-gray-900 border-t border-gray-800 flex-shrink-0">
        <button
          onClick={() => onAdvance(undefined)}
          className="px-4 py-1.5 rounded-lg border border-gray-700 bg-gray-800 text-gray-400 text-sm hover:bg-gray-700 transition-all"
        >
          Bỏ qua →
        </button>
        <span className="text-xs text-gray-600 flex-1 text-center">
          {selected ? "Nhân vật đã chọn" : "Chưa chọn nhân vật"}
        </span>
        <button
          onClick={() => onAdvance(selected ?? undefined)}
          disabled={!selected}
          className="px-4 py-1.5 rounded-lg bg-blue-700 border border-blue-500 text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          Dùng nhân vật này →
        </button>
      </div>
    </div>
  );
}
