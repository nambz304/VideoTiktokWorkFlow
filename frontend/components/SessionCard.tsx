"use client";
import { useRouter } from "next/navigation";
import { deleteSession } from "@/lib/api";
import type { Session } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";
import { vi } from "date-fns/locale";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-700 text-gray-300",
  in_progress: "bg-blue-900 text-blue-300",
  scheduled: "bg-yellow-900 text-yellow-300",
  published: "bg-emerald-900 text-emerald-300",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Nháp",
  in_progress: "Đang làm",
  scheduled: "Đã lên lịch",
  published: "Đã đăng",
};

interface SessionCardProps {
  session: Session;
  onDeleted: () => void;
}

export default function SessionCard({ session, onDeleted }: SessionCardProps) {
  const router = useRouter();

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Xoá session này?")) return;
    await deleteSession(session.id);
    onDeleted();
  }

  return (
    <div
      onClick={() => router.push(`/studio/${session.id}`)}
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 cursor-pointer
        hover:border-gray-600 hover:bg-gray-800 transition-all group"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-semibold text-gray-100 text-sm leading-tight">{session.title}</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${STATUS_STYLES[session.status]}`}>
          {STATUS_LABELS[session.status]}
        </span>
      </div>

      {session.topic && (
        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{session.topic}</p>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">Bước {session.step}/6</span>
          <div className="h-1 w-16 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full"
              style={{ width: `${(session.step / 6) * 100}%` }}
            />
          </div>
        </div>
        <button
          onClick={handleDelete}
          className="text-gray-600 hover:text-red-400 text-xs transition-colors"
        >
          🗑 Xoá
        </button>
      </div>

      <p className="text-xs text-gray-700 mt-2">
        {session.created_at
          ? formatDistanceToNow(new Date(session.created_at), { addSuffix: true, locale: vi })
          : ""}
      </p>
    </div>
  );
}
