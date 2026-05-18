import { create } from 'zustand'
import type { ChatMessage, Conversation, ToolResult } from '../types'

interface ChatState {
  conversations: Conversation[]
  activeConversationId: string | null
  messages: ChatMessage[]
  isStreaming: boolean
  thinkingText: string
  currentActions: ToolResult[]

  setConversations: (conversations: Conversation[]) => void
  setActiveConversation: (id: string) => void
  addMessage: (message: ChatMessage) => void
  setStreaming: (streaming: boolean) => void
  setThinkingText: (text: string) => void
  addAction: (action: ToolResult) => void
  updateAction: (tool: string, update: Partial<ToolResult>) => void
  appendMessageContent: (content: string) => void
  clearCurrentActions: () => void
  newConversation: () => void
}

const generateId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  thinkingText: '',
  currentActions: [],

  setConversations: (conversations) => set({ conversations }),

  setActiveConversation: (id) => set({ activeConversationId: id }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  setThinkingText: (text) => set({ thinkingText: text }),

  addAction: (action) =>
    set((state) => ({ currentActions: [...state.currentActions, action] })),

  updateAction: (tool, update) =>
    set((state) => ({
      currentActions: state.currentActions.map((a) =>
        a.tool === tool ? { ...a, ...update } : a
      ),
    })),

  appendMessageContent: (content) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + content }
      }
      return { messages: msgs }
    }),

  clearCurrentActions: () => set({ currentActions: [], thinkingText: '' }),

  newConversation: () => {
    const id = generateId()
    const conv: Conversation = {
      id,
      title: 'New Conversation',
      project_id: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    set({
      conversations: [conv, ...get().conversations],
      activeConversationId: id,
      messages: [],
      currentActions: [],
      thinkingText: '',
    })
  },
}))
