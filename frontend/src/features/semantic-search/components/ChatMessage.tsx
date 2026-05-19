import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '../../../stores/chat-store';
import { Bot, User, Info } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

const ACTION_STYLE: Record<string, string> = {
  Vector:  'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800',
  Graph:   'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800',
  Hybrid:  'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800',
};

const ACTION_DOT: Record<string, string> = {
  Vector: 'bg-blue-500',
  Graph:  'bg-purple-500',
  Hybrid: 'bg-emerald-500',
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';
  const action = message.metadata?.action_taken ?? '';
  const badgeStyle = ACTION_STYLE[action] ?? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700';
  const dotStyle  = ACTION_DOT[action]  ?? 'bg-gray-400';
  const confidence = message.metadata?.confidence_score;

  return (
    <div className={`flex gap-4 ${isAssistant ? 'bg-gray-50/50 dark:bg-gray-800/30' : ''} p-6 transition-colors`}>
      <div className={`h-10 w-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${
        isAssistant
          ? 'bg-blue-600 text-white'
          : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-500'
      }`}>
        {isAssistant ? <Bot size={22} /> : <User size={22} />}
      </div>

      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-bold text-gray-900 dark:text-white">
            {isAssistant ? 'Graph RAG Assistant' : 'You'}
          </span>

          {isAssistant && action && (
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-tight ${badgeStyle}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${dotStyle}`} />
              {action} Mode
            </span>
          )}

          {isAssistant && confidence != null && (
            <span className="text-[10px] text-gray-400 font-mono">
              {(confidence * 100).toFixed(0)}% conf
            </span>
          )}
        </div>

        <div className="prose dark:prose-invert prose-sm max-w-none text-gray-700 dark:text-gray-300 leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {isAssistant && message.metadata?.routing_reason && (
          <div className="mt-4 p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-800 flex gap-3">
            <Info size={14} className="text-blue-500 shrink-0 mt-0.5" />
            <p className="text-[11px] text-gray-500 italic">
              Routing Logic: {message.metadata.routing_reason}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
