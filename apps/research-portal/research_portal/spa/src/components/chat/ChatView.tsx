import { useEffect, useRef, useCallback } from 'react'
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
  const sseUrlRef = useRef<string | null>(null)
  const assistantMessageIdRef = useRef<string | null>(null)

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
        sseUrlRef.current = null

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
        sseUrlRef.current = null
        appendMessageContent(`\nError: ${JSON.stringify(event.data)}`)
        break
    }
  }, [addAction, updateAction, setThinkingText, appendMessageContent, setStreaming, clearCurrentActions, currentActions.length])

  useSSE(sseUrlRef.current, {
    onEvent: handleSSEEvent,
    onError: () => {
      setStreaming(false)
      sseUrlRef.current = null
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

    sseUrlRef.current = `/api/chat/orchestrate?${params.toString()}`
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#2a2a4a]">
        <h1 className="text-sm font-semibold text-white">AI Research Assistant</h1>
        <Button variant="ghost" size="sm" onClick={newConversation}>
          + New Chat
        </Button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-center text-[#8888aa]">
            <div className="text-4xl mb-4">🧪</div>
            <h2 className="text-lg font-semibold text-white mb-2">Northstar Research Assistant</h2>
            <p className="text-sm max-w-md">
              I can search your research database, extract entities and claims from sources,
              score content quality, visualize knowledge graphs, manage cleanup operations,
              and help with chat imports. What would you like to do?
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-4">
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
                  className="px-3 py-1.5 text-xs bg-[#2a2a4a] text-[#e0e0e0] rounded-full hover:bg-[#3a3a5a] transition-colors"
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
            <div className="w-8 h-8 rounded-full bg-[#2a2a4a] flex items-center justify-center text-sm flex-shrink-0">
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
