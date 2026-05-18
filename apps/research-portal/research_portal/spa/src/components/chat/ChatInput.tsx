import { useState, useRef, useCallback, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const MAX_ROWS = 6
  const ROW_HEIGHT = 24

  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput('')
    textareaRef.current?.focus()
  }, [input, disabled, onSend])

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const lineCount = input.split('\n').length
  const rows = Math.min(Math.max(lineCount, 2), MAX_ROWS)

  return (
    <div className="border-t border-[#2a2a4a] p-4 bg-[#1a1a2e]">
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the AI Researcher anything…"
          className="flex-1 bg-[#16213e] border border-[#2a2a4a] rounded-lg px-4 py-3 text-sm text-[#e0e0e0] placeholder-[#8888aa] resize-none focus:outline-none focus:border-[#e94560] transition-colors disabled:opacity-50"
          rows={rows}
          disabled={disabled}
          style={{ minHeight: `${2 * ROW_HEIGHT + 16}px`, maxHeight: `${MAX_ROWS * ROW_HEIGHT + 16}px` }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="px-5 py-3 bg-[#e94560] text-white rounded-full font-medium text-sm hover:bg-[#d63851] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 self-end flex items-center gap-1.5"
        >
          Send
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
      <p className="text-xs text-[#8888aa] mt-2">
        Enter to send · Shift+Enter for newline
      </p>
    </div>
  )
}
