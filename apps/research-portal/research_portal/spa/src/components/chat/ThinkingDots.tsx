interface ThinkingDotsProps {
  text?: string
}

export function ThinkingDots({ text }: ThinkingDotsProps) {
  return (
    <div className="flex items-center gap-3 text-[#8888aa] text-sm py-2">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-[#e94560] rounded-full animate-bounce opacity-80" style={{ animationDelay: '0ms', animationDuration: '1s' }} />
        <span className="w-2 h-2 bg-[#e94560] rounded-full animate-bounce opacity-60" style={{ animationDelay: '200ms', animationDuration: '1s' }} />
        <span className="w-2 h-2 bg-[#e94560] rounded-full animate-bounce opacity-40" style={{ animationDelay: '400ms', animationDuration: '1s' }} />
      </div>
      {text && <span className="animate-pulse">{text}</span>}
    </div>
  )
}
