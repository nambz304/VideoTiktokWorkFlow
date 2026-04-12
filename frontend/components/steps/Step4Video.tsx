export default function Step4Video({ session, onAdvance, onBack }: any) {
  return (
    <div className="p-6 text-gray-400 text-sm">
      Step 4 — Tạo video (coming soon)
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 bg-gray-700 rounded text-white text-xs">← Back</button>
        <button onClick={onAdvance} className="px-4 py-2 bg-blue-700 rounded text-white text-xs">Next →</button>
      </div>
    </div>
  );
}
