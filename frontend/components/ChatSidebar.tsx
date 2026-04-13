"use client";
import { useState, useRef, useEffect } from "react";
import { sendChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface ChatSidebarProps {
  sessionId: number;
  step: number;
}

export default function ChatSidebar({ sessionId, step }: ChatSidebarProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "ai", text: "Xin chào! Tôi là Milo. Bạn cần hỗ trợ gì không?", timestamp: Date.now() },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text, timestamp: Date.now() }]);
    setLoading(true);
    try {
      const { reply } = await sendChat(sessionId, text, step);
      setMessages((prev) => [...prev, { role: "ai", text: reply, timestamp: Date.now() }]);
    } catch (err) {
      const msg = err instanceof Error && err.message.includes("429")
        ? "Gemini API hết quota. Vui lòng nâng cấp plan hoặc thử lại sau."
        : "Lỗi kết nối, thử lại nhé.";
      setMessages((prev) => [...prev, { role: "ai", text: msg, timestamp: Date.now() }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-72 bg-gray-950 border-l border-gray-800 flex flex-col flex-shrink-0">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-sm font-semibold text-emerald-400">Milo AI</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[90%] px-3 py-2 rounded-xl text-xs leading-relaxed
                ${msg.role === "user"
                  ? "bg-blue-700 text-blue-100 rounded-br-sm"
                  : "bg-gray-800 text-gray-300 rounded-bl-sm"
                }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 px-3 py-2 rounded-xl text-xs text-gray-400">...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-gray-800">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ra lệnh hoặc hỏi Milo..."
            rows={2}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200
              placeholder-gray-500 outline-none focus:border-blue-500 resize-none"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="w-8 h-8 bg-blue-700 rounded-lg flex items-center justify-center flex-shrink-0
              hover:bg-blue-600 disabled:opacity-30 transition-all self-end"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-1.5">VD: &quot;làm lại cảnh 2&quot; · &quot;đổi hashtag&quot;</p>
      </div>
    </div>
  );
}
