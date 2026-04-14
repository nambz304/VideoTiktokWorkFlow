"use client";
import { useState } from "react";
import { fetchTrends, generateScripts, updateSession } from "@/lib/api";
import NavBar from "@/components/NavBar";
import type { Session, TrendTopic } from "@/lib/types";

type SubStep = "trends" | "topic" | "scripts";

export default function Step1Trend({ session, onAdvance }: { session: Session; onAdvance: () => void }) {
  const [subStep, setSubStep] = useState<SubStep>("trends");
  const [trends, setTrends] = useState<TrendTopic[]>([]);
  const [topic, setTopic] = useState(session.topic ?? "");
  const [scripts, setScripts] = useState<string[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [trendError, setTrendError] = useState<string | null>(null);

  async function loadTrends() {
    setLoading(true);
    setTrendError(null);
    try {
      const data = await fetchTrends(session.id);
      setTrends(data);
      setSubStep("trends");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setTrendError(msg.includes("429") ? "Google Trends giới hạn request (429). Hãy nhập chủ đề thủ công." : `Lỗi: ${msg}`);
    } finally {
      setLoading(false);
    }
  }

  async function confirmTopic() {
    await updateSession(session.id, { topic });
    setSubStep("scripts");
    setLoading(true);
    try {
      const data = await generateScripts(session.id);
      setScripts(data.scripts);
    } finally {
      setLoading(false);
    }
  }

  async function confirmScript() {
    if (selected === null) return;
    await updateSession(session.id, { topic, status: "in_progress", script: scripts[selected] });
    onAdvance();
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-1">Bước 1 — Kịch bản</h2>

        {/* SUB-STEP NAV */}
        <div className="flex gap-3 mb-5">
          {(["trends", "topic", "scripts"] as SubStep[]).map((s, i) => (
            <div key={s} className={`flex items-center gap-2 text-xs ${subStep === s ? "text-blue-300 font-semibold" : "text-gray-600"}`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold
                ${subStep === s ? "bg-blue-700 text-white" : "bg-gray-800 text-gray-500"}`}>{i + 1}</span>
              {s === "trends" ? "Trend research" : s === "topic" ? "Chọn chủ đề" : "Chọn kịch bản"}
            </div>
          ))}
        </div>

        {/* 1A: TREND LIST */}
        {subStep === "trends" && (
          <div>
            <p className="text-sm text-gray-400 mb-4">Fetch trends đang hot về sức khoẻ + AI.</p>
            {trends.length === 0 ? (
              <div className="space-y-3">
                <button onClick={loadTrends} disabled={loading}
                  className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50">
                  {loading ? "Đang tìm..." : "🔍 Fetch trends"}
                </button>
                {trendError && (
                  <div className="text-xs text-amber-400 bg-amber-900/20 border border-amber-800 rounded-lg px-4 py-3">
                    {trendError}
                  </div>
                )}
                <button onClick={() => setSubStep("topic")}
                  className={`px-4 py-2 border rounded-lg text-sm transition-all
                    ${trendError
                      ? "border-blue-600 text-blue-300 bg-blue-900/20 hover:bg-blue-900/40"
                      : "border-gray-700 text-gray-400 hover:bg-gray-800"}`}>
                  ✏️ Tự nhập chủ đề →
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {trends.map((t, i) => (
                  <div key={i} onClick={() => { setTopic(t.topic); setSubStep("topic"); }}
                    className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 cursor-pointer hover:border-gray-600 transition-all">
                    <div>
                      <p className="text-sm text-gray-200">{t.topic}</p>
                      <p className="text-xs text-gray-500">{t.source}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-1 w-12 bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${t.score}%` }} />
                      </div>
                      <span className="text-xs text-gray-500">{t.score}</span>
                    </div>
                  </div>
                ))}
                <button onClick={() => setSubStep("topic")}
                  className="mt-3 px-4 py-2 border border-gray-700 rounded-lg text-sm text-gray-300 hover:bg-gray-800">
                  Tự nhập chủ đề →
                </button>
              </div>
            )}
          </div>
        )}

        {/* 1B: TOPIC CONFIRM */}
        {subStep === "topic" && (
          <div>
            <p className="text-sm text-gray-400 mb-4">Xác nhận hoặc chỉnh lại chủ đề trước khi tạo kịch bản.</p>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Nhập hoặc chỉnh chủ đề video..."
              rows={3}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm text-gray-200
                placeholder-gray-500 outline-none focus:border-blue-500 resize-none mb-4"
            />
            <button onClick={confirmTopic} disabled={!topic.trim() || loading}
              className="px-4 py-2 bg-blue-700 rounded-lg text-sm text-white disabled:opacity-50">
              {loading ? "Đang tạo kịch bản..." : "✓ Xác nhận & tạo kịch bản"}
            </button>
          </div>
        )}

        {/* 1C: SCRIPT SELECT */}
        {subStep === "scripts" && (
          <div>
            {loading ? (
              <div className="flex items-center gap-3 text-sm text-gray-400 py-6">
                <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                Đang tạo các kịch bản mẫu...
              </div>
            ) : (
              <>
                <p className="text-sm text-gray-400 mb-4">Chọn 1 kịch bản để tiếp tục. Có thể chỉnh sửa trực tiếp.</p>
                <div className="space-y-3">
                  {scripts.map((script, i) => (
                    <div key={i} onClick={() => setSelected(i)}
                      className={`bg-gray-900 border rounded-xl p-4 cursor-pointer transition-all
                        ${selected === i ? "border-blue-500" : "border-gray-800 hover:border-gray-600"}`}>
                      <div className="text-xs text-gray-500 font-semibold mb-2">Kịch bản {i + 1}</div>
                      <pre className="text-xs text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{script}</pre>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <NavBar
        step={1} totalSteps={6}
        onBack={() => {}}
        onNext={subStep === "trends" && trends.length > 0 ? () => setSubStep("topic")
          : subStep === "topic" ? confirmTopic
          : confirmScript}
        nextDisabled={loading}
        nextLabel={subStep === "scripts" ? "OK, qua Bước 2 →" : "Tiếp →"}
      />
    </div>
  );
}
