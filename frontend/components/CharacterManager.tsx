'use client'

import { useState, useEffect, useRef } from 'react'
import { Character } from '@/lib/types'

interface Props {
  selectedId: number | null
  onSelect: (char: Character) => void
}

export default function CharacterManager({ selectedId, onSelect }: Props) {
  const [characters, setCharacters] = useState<Character[]>([])
  const [creating, setCreating] = useState(false)
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState('')
  const [personality, setPersonality] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const fileRef = useRef<HTMLInputElement>(null)

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${API}/characters/`)
      .then(r => r.json())
      .then(d => setCharacters(d.characters || []))
  }, [])

  async function createCharacter() {
    if (!name.trim()) return
    setLoading(true)
    const form = new FormData()
    form.append('name', name)
    form.append('personality', personality)
    files.forEach(f => form.append('files', f))

    const res = await fetch(`${API}/characters/`, { method: 'POST', body: form })
    const char: Character = await res.json()
    setCharacters(prev => [char, ...prev])
    setCreating(false)
    setName('')
    setPersonality('')
    setFiles([])
    setLoading(false)
    onSelect(char)
  }

  async function deleteCharacter(id: number) {
    await fetch(`${API}/characters/${id}`, { method: 'DELETE' })
    setCharacters(prev => prev.filter(c => c.id !== id))
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Nhân vật</h3>
        <button
          onClick={() => setCreating(true)}
          className="text-xs bg-indigo-600 hover:bg-indigo-500 px-3 py-1 rounded-full text-white"
        >
          + Thêm nhân vật
        </button>
      </div>

      {/* Character list */}
      <div className="space-y-2">
        {characters.map(char => (
          <div
            key={char.id}
            onClick={() => onSelect(char)}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedId === char.id
                ? 'border-indigo-500 bg-indigo-900/30'
                : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-lg">
              🤖
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-200 truncate">{char.name}</div>
              <div className="text-xs text-gray-500 truncate">
                {char.ref_image_count} ảnh ref
                {char.fal_ready ? ' · ✓ sẵn sàng' : ' · ⏳ chưa upload'}
              </div>
            </div>
            {selectedId === char.id && (
              <span className="text-xs text-indigo-400 font-semibold">✓ Đang dùng</span>
            )}
            <button
              onClick={e => { e.stopPropagation(); deleteCharacter(char.id) }}
              className="text-gray-600 hover:text-red-400 text-xs px-1"
            >
              ✕
            </button>
          </div>
        ))}

        {characters.length === 0 && !creating && (
          <p className="text-xs text-gray-600 text-center py-4">
            Chưa có nhân vật nào. Thêm nhân vật để bắt đầu.
          </p>
        )}
      </div>

      {/* Create form */}
      {creating && (
        <div className="border border-indigo-500/40 bg-indigo-900/20 rounded-lg p-4 space-y-3">
          <div className="text-xs font-semibold text-indigo-300">Tạo nhân vật mới</div>

          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Tên nhân vật (vd: Milo)"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600"
          />

          <textarea
            value={personality}
            onChange={e => setPersonality(e.target.value)}
            placeholder="Mô tả tính cách: Robot vui vẻ, hài hước, thích nhảy nhót..."
            rows={2}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 resize-none"
          />

          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={e => setFiles(Array.from(e.target.files || []).slice(0, 3))}
            />
            <button
              onClick={() => fileRef.current?.click()}
              className="w-full border border-dashed border-gray-600 rounded py-3 text-xs text-gray-500 hover:border-gray-400 hover:text-gray-400"
            >
              {files.length > 0
                ? `✓ ${files.length} ảnh đã chọn`
                : '📸 Upload 1-3 ảnh reference'}
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={createCharacter}
              disabled={loading || !name.trim()}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2 rounded text-sm font-semibold text-white"
            >
              {loading ? 'Đang tạo...' : 'Tạo nhân vật'}
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
  )
}
