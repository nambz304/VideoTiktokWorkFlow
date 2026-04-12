export default function Step6Publish({ session, onBack }: any) {
  return (
    <div className="p-6 text-gray-400 text-sm">
      Step 6 — Đăng bài (coming soon)
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 bg-gray-700 rounded text-white text-xs">← Back</button>
      </div>
    </div>
  );
}
