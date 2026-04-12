"use client";

interface NavBarProps {
  step: number;
  totalSteps: number;
  approvedCount?: number;
  totalCount?: number;
  onBack: () => void;
  onNext: () => void;
  nextDisabled?: boolean;
  nextLabel?: string;
}

export default function NavBar({
  step, totalSteps, approvedCount, totalCount,
  onBack, onNext, nextDisabled, nextLabel,
}: NavBarProps) {
  return (
    <div className="flex items-center gap-3 px-6 py-3 bg-gray-900 border-t border-gray-800 flex-shrink-0">
      <button
        onClick={onBack}
        disabled={step === 1}
        className="px-4 py-1.5 rounded-lg border border-gray-700 bg-gray-800 text-gray-300 text-sm
          hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        ← Bước trước
      </button>

      <span className="text-xs text-gray-500 flex-1 text-center">
        Bước {step} / {totalSteps}
        {approvedCount !== undefined && totalCount !== undefined && (
          <> · {approvedCount}/{totalCount} đã approve</>
        )}
      </span>

      <button
        onClick={onNext}
        disabled={nextDisabled}
        className="px-4 py-1.5 rounded-lg bg-blue-700 border border-blue-500 text-white text-sm font-medium
          hover:bg-blue-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        {nextLabel ?? "Tiếp theo →"}
      </button>
    </div>
  );
}
