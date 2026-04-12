"use client";
import ScheduleCalendar from "@/components/ScheduleCalendar";
import { useRouter } from "next/navigation";

export default function SchedulePage() {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-bold text-gray-100">📅 Lịch đăng</h1>
            <p className="text-sm text-gray-500 mt-0.5">Các video đã lên lịch và đã đăng</p>
          </div>
          <button onClick={() => router.push("/sessions")}
            className="px-4 py-2 rounded-lg border border-gray-700 bg-gray-800 text-gray-300 text-sm hover:bg-gray-700">
            ← Sessions
          </button>
        </div>
        <ScheduleCalendar />
      </div>
    </div>
  );
}
