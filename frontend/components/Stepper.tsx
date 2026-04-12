"use client";

const STEPS = [
  { n: 1, label: "Kịch bản" },
  { n: 2, label: "Phân cảnh" },
  { n: 3, label: "Chọn ảnh" },
  { n: 4, label: "Video cảnh" },
  { n: 5, label: "Ghép video" },
  { n: 6, label: "Xuất & Đăng" },
];

export default function Stepper({ currentStep }: { currentStep: number }) {
  return (
    <div className="flex items-center gap-0 px-6 py-3 bg-gray-900 border-b border-gray-800">
      {STEPS.map((step, i) => {
        const done = step.n < currentStep;
        const active = step.n === currentStep;
        return (
          <div key={step.n} className="flex items-center flex-1">
            <div className="flex items-center gap-1.5 min-w-0">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 border-2 transition-all
                  ${done ? "bg-emerald-900 border-emerald-400 text-emerald-400" : ""}
                  ${active ? "bg-blue-700 border-blue-400 text-white shadow-[0_0_12px_rgba(59,130,246,0.4)]" : ""}
                  ${!done && !active ? "bg-gray-800 border-gray-600 text-gray-500" : ""}
                `}
              >
                {done ? "✓" : step.n}
              </div>
              <span
                className={`text-xs truncate
                  ${done ? "text-emerald-400" : ""}
                  ${active ? "text-blue-300 font-semibold" : ""}
                  ${!done && !active ? "text-gray-500" : ""}
                `}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-0.5 flex-1 mx-2 ${done ? "bg-emerald-800" : "bg-gray-800"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
