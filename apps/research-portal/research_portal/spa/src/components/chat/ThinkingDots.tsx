interface ThinkingDotsProps {
  text?: string
}

export function ThinkingDots({ text }: ThinkingDotsProps) {
  return (
    <div className="flex items-center gap-2 text-[#8888aa] text-sm py-2">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-[#e94560] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 bg-[#e94560] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 bg-[#e94560] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      {text && <span>{text}</span>}
    </div>
  )
}
