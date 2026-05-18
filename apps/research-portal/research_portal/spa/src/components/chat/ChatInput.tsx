import { useState, useRef, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput('')
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-[#2a2a4a] p-4">
      <div className="flex gap-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the AI Researcher anything… (e.g., 'Find sources about quantum computing and score them')"
          className="flex-1 bg-[#16213e] border border-[#2a2a4a] rounded-lg px-4 py-3 text-sm text-[#e0e0e0] placeholder-[#8888aa] resize-none focus:outline-none focus:border-[#e94560] transition-colors"
          rows={2}
          disabled={disabled}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="px-4 py-3 bg-[#e94560] text-white rounded-lg font-medium text-sm hover:bg-[#d63851] disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
        >
          Send
        </button>
      </div>
      <p className="text-xs text-[#8888aa] mt-2">
        Enter to send · Shift+Enter for newline · The AI can search, extract, score, and manage your research
      </p>
    </div>
  )
}
