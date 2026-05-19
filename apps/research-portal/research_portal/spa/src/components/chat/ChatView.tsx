import { useEffect, useRef, useCallback, useState } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { useSSE } from '../../hooks/useSSE'
import { MessageBubble } from './MessageBubble'
import { ThinkingDots } from './ThinkingDots'
import { ChatInput } from './ChatInput'
import { Button } from '../shared/Button'
import type { SSEEvent, ChatMessage } from '../../types'

export function ChatView() {
  const {
    messages,
    isStreaming,
    thinkingText,
    currentActions,
    addMessage,
    setStreaming,
    setThinkingText,
    addAction,
    updateAction,
    appendMessageContent,
    clearCurrentActions,
    conversations,
    activeConversationId,
    newConversation,
  } = useChatStore()

  const scrollRef = useRef<HTMLDivElement>(null)
  const assistantMessageIdRef = useRef<string | null>(null)
  const [sseUrl, setSseUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!activeConversationId && conversations.length === 0) {
      newConversation()
    }
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinkingText, currentActions])

  const handleSSEEvent = useCallback((event: SSEEvent) => {
    switch (event.event) {
      case 'thinking':
        setThinkingText(String(event.data.text || ''))
        break

      case 'action': {
        const tool = String(event.data.action || event.data.tool || '')
        const status = String(event.data.status || 'running')
        addAction({ tool, type: '', status: status as 'running' | 'completed' | 'failed', data: event.data })
        break
      }

      case 'result': {
        const tool = String(event.data.action || event.data.tool || '')
        updateAction(tool, {
          status: 'completed',
          type: String(event.data.type || ''),
          data: event.data.data || event.data,
        })

        const content = String(event.data.summary || event.data.content || '')
        if (content) {
          appendMessageContent(content + '\n')
        }
        break
      }

      case 'done': {
        setStreaming(false)
        setSseUrl(null)

        if (assistantMessageIdRef.current && currentActions.length > 0) {
          const msg = useChatStore.getState().messages.find(
            (m) => m.id === assistantMessageIdRef.current
          )
          if (msg) {
            const merged = {
              ...msg,
              tool_results: [...useChatStore.getState().currentActions],
            }
            useChatStore.setState((state) => ({
              messages: state.messages.map((m) =>
                m.id === assistantMessageIdRef.current ? merged : m
              ),
            }))
          }
        }
        clearCurrentActions()
        assistantMessageIdRef.current = null
        break
      }

      case 'error':
        setStreaming(false)
        setSseUrl(null)
        appendMessageContent(`\nError: ${JSON.stringify(event.data)}`)
        break
    }
  }, [addAction, updateAction, setThinkingText, appendMessageContent, setStreaming, clearCurrentActions, currentActions.length])

  useSSE(sseUrl, {
    onEvent: handleSSEEvent,
    onError: () => {
      setStreaming(false)
      setSseUrl(null)
    },
  })

  const generateId = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID()
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0
      return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
    })
  }

  const handleSend = async (text: string) => {
    if (isStreaming) return

    const msgId = generateId()
    const userMsg: ChatMessage = {
      id: msgId,
      conversation_id: activeConversationId || '',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    addMessage(userMsg)

    const assistantMsgId = generateId()
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      conversation_id: activeConversationId || '',
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    }
    addMessage(assistantMsg)
    assistantMessageIdRef.current = assistantMsgId

    setStreaming(true)
    clearCurrentActions()

    const params = new URLSearchParams()
    params.set('message', text)
    if (activeConversationId) params.set('conversation_id', activeConversationId)

    setSseUrl(`/api/chat/orchestrate?${params.toString()}`)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-3 border-b border-[#2a2a4a]">
        <h1 className="text-sm font-semibold text-white">AI Research Assistant</h1>
        <Button variant="ghost" size="sm" onClick={newConversation}>
          + New Chat
        </Button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-center text-[#8888aa]">
            <svg
              className="w-12 h-12 mb-4 text-[#e94560]/40"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
            </svg>
            <h2 className="text-lg font-semibold text-white mb-2">Northstar Research Assistant</h2>
            <p className="text-sm max-w-md leading-relaxed">
              I can search your research database, extract entities and claims from sources,
              score content quality, visualize knowledge graphs, manage cleanup operations,
              and help with chat imports. What would you like to do?
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-6 max-w-lg">
              {[
                'List all projects and their sources',
                'Extract entities from my latest source',
                'Score the quality of all sources',
                'Show me the cleanup report',
                'Search for quantum computing',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleSend(suggestion)}
                  className="px-4 py-2 text-xs bg-[#2a2a4a]/60 text-[#e0e0e0] rounded-full hover:bg-[#3a3a5a] hover:text-white hover:border-[#e94560]/30 transition-all duration-150 border border-transparent"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isStreaming && thinkingText && (
          <div className="flex gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-[#2a2a4a] flex items-center justify-center text-sm font-bold flex-shrink-0">
              AI
            </div>
            <div className="bg-[#16213e] border border-[#2a2a4a] rounded-lg px-4 py-2.5">
              <ThinkingDots text={thinkingText} />
            </div>
          </div>
        )}
      </div>

      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  )
}
