"use client";
import useSWR from "swr";
import { listSchedule } from "@/lib/api";
import { format, parseISO } from "date-fns";
import { vi } from "date-fns/locale";

export default function ScheduleCalendar() {
  const { data: entries } = useSWR("schedule", listSchedule);

  const STATUS_STYLE: Record<string, string> = {
    pending: "bg-yellow-900 text-yellow-300",
    scheduled: "bg-blue-900 text-blue-300",
    published: "bg-emerald-900 text-emerald-300",
    failed: "bg-red-900 text-red-300",
  };

  if (!entries) return <p className="text-gray-600 text-sm p-6">Đang tải...</p>;
  if (entries.length === 0) return <p className="text-gray-600 text-sm p-6">Chưa có video nào được lên lịch.</p>;

  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div key={entry.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-200 mb-1">
                📅 {format(parseISO(entry.post_time), "EEEE, dd/MM/yyyy HH:mm", { locale: vi })}
              </div>
              {entry.caption && (
                <p className="text-xs text-gray-500 line-clamp-2">{entry.caption}</p>
              )}
              {entry.hashtags && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {JSON.parse(entry.hashtags ?? "[]").slice(0, 5).map((tag: string, i: number) => (
                    <span key={i} className="text-xs px-2 py-0.5 bg-gray-800 text-blue-400 rounded-full">{tag}</span>
                  ))}
                </div>
              )}
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${STATUS_STYLE[entry.status] ?? ""}`}>
              {entry.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
