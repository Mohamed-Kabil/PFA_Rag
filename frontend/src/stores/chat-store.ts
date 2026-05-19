import { create } from 'zustand';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  metadata?: {
    action_taken: string;
    confidence_score: number;
    sources: any[];
    routing_reason?: string;
    retrieval_summary?: any;
    decision_path?: any[];
    q_values?: Record<string, number>;
  };
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setLoading: (loading) => set({ isLoading: loading }),
  clearChat: () => set({ messages: [] }),
}));
