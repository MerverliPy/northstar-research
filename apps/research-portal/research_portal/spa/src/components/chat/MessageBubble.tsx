import type { ChatMessage } from '../../types'
import { ResultCard } from './ResultCard'

interface MessageBubbleProps {
  message: ChatMessage
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
    <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
          isUser ? 'bg-[#e94560]' : 'bg-[#2a2a4a]'
        }`}
      >
        {isUser ? 'U' : 'AI'}
      </div>
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? 'bg-[#e94560] text-white'
              : 'bg-[#16213e] text-[#e0e0e0] border border-[#2a2a4a]'
          }`}
        >
          {message.content ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <span className="text-[#8888aa] italic">Thinking…</span>
          )}
        </div>
        {message.tool_results?.map((result, i) => (
          <ResultCard key={`${result.tool}-${i}`} result={result} />
        ))}
      </div>
    </div>
  )
}
