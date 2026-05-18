import { useState, useCallback } from 'react'
import type { ChatMessage } from '../../types'
import { ResultCard } from './ResultCard'

interface MessageBubbleProps {
  message: ChatMessage
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const copy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [text])

  return (
    <button
      onClick={copy}
      className="text-[#8888aa] hover:text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity"
      title="Copy message"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <span className="text-xs text-[#8888aa] bg-[#2a2a4a]/30 px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    )
  }

  return (
    <div className={`flex gap-3 mb-4 group ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
          isUser ? 'bg-[#e94560] text-white' : 'bg-[#2a2a4a] text-[#e0e0e0]'
        }`}
      >
        {isUser ? 'U' : 'AI'}
      </div>
      <div className={`max-w-[80%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? 'bg-[#e94560] text-white'
              : 'bg-[#16213e] text-[#e0e0e0] border border-[#2a2a4a]'
          }`}
        >
          {message.content ? (
            <div className="whitespace-pre-wrap break-words">{message.content}</div>
          ) : (
            <span className="text-[#8888aa] italic">Thinking...</span>
          )}
        </div>
        <div className={`flex items-center gap-2 mt-1 px-1 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="text-[10px] text-[#8888aa]/60">{formatTime(message.created_at)}</span>
          {message.content && <CopyButton text={message.content} />}
        </div>
        {message.tool_results?.map((result, i) => (
          <ResultCard key={`${result.tool}-${i}`} result={result} />
        ))}
      </div>
    </div>
  )
}
