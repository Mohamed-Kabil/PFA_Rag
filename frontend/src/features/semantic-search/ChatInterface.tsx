import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChatStore } from '../../stores/chat-store';
import { searchService } from '../../services/api-service';
import { ChatMessage } from './components/ChatMessage';
import { RetrievalPanel } from './components/RetrievalPanel';
import {
  Send, Trash2, Loader2, Sparkles, Bot,
  History, Zap, ArrowRight, Clock,
} from 'lucide-react';

const ACTION_COLOR: Record<string, string> = {
  Vector: '#3b82f6',
  Graph:  '#a855f7',
  Hybrid: '#10b981',
};

const ACTION_BG: Record<string, string> = {
  Vector: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300',
  Graph:  'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-300',
  Hybrid: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300',
};

interface RoutingPreview {
  predicted_action: string;
  confidence: number;
  reason: string;
}

export const ChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const { messages, addMessage, isLoading, setLoading, clearChat } = useChatStore();
  const [activeMessageIndex, setActiveMessageIndex] = useState<number | null>(null);
  const [sideTab, setSideTab] = useState<'trace' | 'history'>('trace');
  const [routingPreview, setRoutingPreview] = useState<RoutingPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Debounced routing preview
  const fetchPreview = useCallback(async (q: string) => {
    if (q.trim().length < 8) { setRoutingPreview(null); return; }
    setPreviewLoading(true);
    try {
      const data = await searchService.preview(q);
      setRoutingPreview({
        predicted_action: data.predicted_action ?? data.action_taken ?? 'Hybrid',
        confidence: data.confidence ?? data.confidence_score ?? 0,
        reason: data.reason ?? data.routing_reason ?? '',
      });
    } catch {
      setRoutingPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!input.trim()) { setRoutingPreview(null); return; }
    debounceRef.current = setTimeout(() => fetchPreview(input), 500);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [input, fetchPreview]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');
    setRoutingPreview(null);
    addMessage({ role: 'user', content: userMessage });
    setLoading(true);

    try {
      const data = await searchService.query(userMessage);
      const assistantMessage = {
        role: 'assistant' as const,
        content: data.answer,
        metadata: {
          action_taken: data.action_taken,
          confidence_score: data.confidence_score,
          sources: data.sources,
          routing_reason: data.routing_reason,
          retrieval_summary: data.retrieval_summary,
          decision_path: data.decision_path,
          q_values: data.q_values,
        }
      };
      addMessage(assistantMessage);
      setActiveMessageIndex(messages.length + 1);
      setSideTab('trace');
    } catch (error) {
      console.error("Chat Error:", error);
      addMessage({
        role: 'assistant',
        content: "I'm sorry, I encountered an error while processing your request. Please ensure the backend is running."
      });
    } finally {
      setLoading(false);
    }
  };

  const currentAssistantMessage = activeMessageIndex !== null ? messages[activeMessageIndex] : null;

  // Query history: pairs of (user query, assistant response)
  const queryHistory = React.useMemo(() => {
    const pairs: { query: string; action: string; confidence: number; index: number }[] = [];
    for (let i = 0; i < messages.length - 1; i++) {
      if (messages[i].role === 'user' && messages[i + 1]?.role === 'assistant') {
        pairs.push({
          query: messages[i].content,
          action: messages[i + 1].metadata?.action_taken ?? '—',
          confidence: messages[i + 1].metadata?.confidence_score ?? 0,
          index: i + 1,
        });
      }
    }
    return pairs.reverse();
  }, [messages]);

  return (
    <div className="h-[calc(100vh-120px)] flex gap-6">
      {/* ── Main Chat Area ── */}
      <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-white dark:bg-gray-900 z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 rounded-lg">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-gray-900 dark:text-white leading-none">AI Research Assistant</h2>
              <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Graph RAG Intelligence</span>
            </div>
          </div>
          <button
            onClick={clearChat}
            className="p-2 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/20 rounded-lg text-gray-400 transition-colors"
            title="Clear Conversation"
          >
            <Trash2 size={18} />
          </button>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-2 bg-white dark:bg-gray-950">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center p-12 text-center">
              <div className="w-20 h-20 bg-blue-50 dark:bg-blue-900/10 rounded-3xl flex items-center justify-center mb-6 text-blue-600">
                <Bot size={40} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Welcome to Graph RAG Explorer</h3>
              <p className="text-gray-500 dark:text-gray-400 max-w-sm text-sm">
                Ask anything about your knowledge base. I'll use a combination of vector search and graph analysis to provide cited, accurate answers.
              </p>
              <div className="mt-8 flex flex-wrap gap-2 justify-center">
                {[
                  "Impact de la fragmentation ?",
                  "Comment les espèces survivent ?",
                  "List key climate policies",
                  "C'est quoi la meilleure méthode de chunking/embedding dans notre projet?",
                ].map((hint) => (
                  <button
                    key={hint}
                    onClick={() => setInput(hint)}
                    className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-xs font-medium text-gray-600 dark:text-gray-400 hover:border-blue-300 transition-all"
                  >
                    {hint}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              onClick={() => { if (msg.role === 'assistant') { setActiveMessageIndex(idx); setSideTab('trace'); } }}
              className={msg.role === 'assistant' ? 'cursor-pointer' : ''}
            >
              <ChatMessage message={msg} />
            </div>
          ))}
          {isLoading && (
            <div className="p-6 flex gap-4">
              <div className="h-10 w-10 bg-blue-50 dark:bg-blue-900/30 rounded-xl flex items-center justify-center shrink-0">
                <Loader2 size={18} className="text-blue-500 animate-spin" />
              </div>
              <div className="flex flex-col gap-1.5 justify-center">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Generating answer…</p>
                <p className="text-[11px] text-gray-400">Running retrieval + local LLM on CPU — this can take 1–3 minutes. Please wait.</p>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-6 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 space-y-2">

          {/* ── Routing Preview Indicator (#35) ── */}
          {(routingPreview || previewLoading) && (
            <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px] transition-all ${
              routingPreview
                ? (ACTION_BG[routingPreview.predicted_action] ?? 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400')
                : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-400'
            }`}>
              {previewLoading ? (
                <>
                  <Loader2 size={11} className="animate-spin shrink-0" />
                  <span>Analyzing routing…</span>
                </>
              ) : routingPreview ? (
                <>
                  <Zap size={11} className="shrink-0" />
                  <span className="font-bold">Expected routing:</span>
                  <span
                    className="font-black uppercase tracking-wide px-1.5 py-0.5 rounded"
                    style={{ background: (ACTION_COLOR[routingPreview.predicted_action] ?? '#64748b') + '22', color: ACTION_COLOR[routingPreview.predicted_action] ?? '#64748b' }}
                  >
                    {routingPreview.predicted_action}
                  </span>
                  <span className="font-mono text-gray-400">
                    {(routingPreview.confidence * 100).toFixed(0)}% conf
                  </span>
                  {routingPreview.reason && (
                    <>
                      <ArrowRight size={10} className="text-gray-300 shrink-0" />
                      <span className="italic truncate text-gray-400">{routingPreview.reason}</span>
                    </>
                  )}
                </>
              ) : null}
            </div>
          )}

          <form onSubmit={handleSendMessage} className="relative">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e as unknown as React.FormEvent);
                }
              }}
              placeholder="Ask a question..."
              className="w-full pl-4 pr-14 py-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-sm"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-blue-600 text-white rounded-xl shadow-lg shadow-blue-500/30 hover:bg-blue-700 disabled:bg-gray-300 disabled:shadow-none transition-all"
            >
              {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </form>

          <p className="text-center text-[10px] text-gray-400">
            Agentic Graph RAG: Dynamically routing between Vector and Neo4j.
          </p>
        </div>
      </div>

      {/* ── Right Panel: Trace / History ── */}
      <div className="w-96 bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden flex flex-col">

        {/* Tab bar */}
        <div className="flex border-b border-gray-100 dark:border-gray-800">
          {([
            { key: 'trace',   label: 'Intelligence', Icon: Zap },
            { key: 'history', label: 'History',       Icon: History },
          ] as const).map(({ key, label, Icon }) => (
            <button
              key={key}
              onClick={() => setSideTab(key)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-bold transition-colors ${
                sideTab === key
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50 dark:bg-blue-900/10'
                  : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              <Icon size={13} />
              {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-hidden">
          {sideTab === 'trace' ? (
            <RetrievalPanel activeMessage={currentAssistantMessage} />
          ) : (
            /* ── Query History panel (#36) ── */
            <div className="h-full flex flex-col overflow-y-auto">
              {queryHistory.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-gray-400">
                  <Clock size={32} className="mb-4 opacity-40" />
                  <p className="text-sm font-bold text-gray-900 dark:text-white mb-1">No history yet</p>
                  <p className="text-xs">Your query history will appear here after each interaction.</p>
                </div>
              ) : (
                <div className="p-4 space-y-3">
                  <p className="text-[10px] uppercase font-bold text-gray-400 tracking-widest px-1">
                    {queryHistory.length} {queryHistory.length === 1 ? 'Query' : 'Queries'}
                  </p>
                  {queryHistory.map((item, i) => (
                    <button
                      key={i}
                      onClick={() => { setActiveMessageIndex(item.index); setSideTab('trace'); }}
                      className="w-full text-left p-3 bg-gray-50 dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-blue-900/10 border border-gray-100 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-800 rounded-xl transition-colors group"
                    >
                      {/* Query text */}
                      <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2 mb-2 group-hover:text-gray-900 dark:group-hover:text-white">
                        {item.query}
                      </p>
                      {/* Badges */}
                      <div className="flex items-center gap-2">
                        <span
                          className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                          style={{
                            background: (ACTION_COLOR[item.action] ?? '#64748b') + '22',
                            color: ACTION_COLOR[item.action] ?? '#64748b',
                          }}
                        >
                          {item.action}
                        </span>
                        <span className="text-[10px] text-gray-400 font-mono">
                          {(item.confidence * 100).toFixed(0)}% conf
                        </span>
                        <ArrowRight size={10} className="text-gray-300 ml-auto" />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
