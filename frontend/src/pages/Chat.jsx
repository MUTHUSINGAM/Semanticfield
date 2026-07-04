import { useState, useRef, useEffect } from 'react';
import { Send, Shield, AlertTriangle, CheckCircle, Ban } from 'lucide-react';
import { chatAPI } from '../api/client';

const ACTION_STYLES = {
  allow: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-400/10' },
  mask: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
  block: { icon: Ban, color: 'text-red-400', bg: 'bg-red-400/10' },
  human_review: { icon: Shield, color: 'text-purple-400', bg: 'bg-purple-400/10' },
};

const RISK_COLORS = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' };

const SUGGESTIONS = [
  "What is Ravi's salary?",
  'Share the Q3 revenue forecast',
  'What is on the 2026 product roadmap?',
  'What is the Acme Corp contract value?',
];

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hello! I\'m the Singam Technologies AI Assistant, protected by SemanticShield AI. Ask me anything — every response is inspected for confidential data leaks before delivery.',
      meta: null,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    const msg = text || input;
    if (!msg.trim() || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const res = await chatAPI.send(msg);
      const data = res.data;
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.final_response,
          meta: data,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: err.response?.data?.detail || 'Error processing request.',
          meta: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="p-6 border-b border-shield-700/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-shield-accent/20 rounded-lg flex items-center justify-center">
            <Shield className="w-4 h-4 text-shield-accent" />
          </div>
          <div>
            <h1 className="text-lg font-bold">AI Assistant</h1>
            <p className="text-xs text-gray-500">Protected by SemanticShield · Real-time DLP inspection</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-2xl rounded-xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-shield-accent text-white'
                  : 'bg-shield-900 border border-shield-700/50'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

              {msg.meta && (
                <div className="mt-3 pt-3 border-t border-shield-700/50 space-y-2">
                  <div className="flex flex-wrap gap-2">
                    <span
                      className="text-xs px-2 py-0.5 rounded-full font-medium"
                      style={{
                        background: `${RISK_COLORS[msg.meta.risk_level]}20`,
                        color: RISK_COLORS[msg.meta.risk_level],
                      }}
                    >
                      Risk: {msg.meta.risk_level} ({msg.meta.risk_score})
                    </span>
                    {(() => {
                      const style = ACTION_STYLES[msg.meta.action] || ACTION_STYLES.allow;
                      const Icon = style.icon;
                      return (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1 ${style.bg} ${style.color}`}>
                          <Icon className="w-3 h-3" />
                          {msg.meta.action.toUpperCase()}
                        </span>
                      );
                    })()}
                    {msg.meta.leak_detected && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-red-400/10 text-red-400">
                        Leak Detected
                      </span>
                    )}
                  </div>
                  {msg.meta.verification_reason && (
                    <p className="text-xs text-gray-500">{msg.meta.verification_reason}</p>
                  )}
                  {msg.meta.matched_documents?.length > 0 && (
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>
                        Matched: {msg.meta.matched_documents.map((d) => `${d.source} (${(d.similarity * 100).toFixed(0)}%)`).join(', ')}
                      </div>
                      {msg.meta.matched_documents[0]?.resource_uri && (
                        <div className="font-mono text-purple-400/80">
                          MCP: {msg.meta.matched_documents[0].resource_uri}
                          {msg.meta.matched_documents[0].connection_type && (
                            <span className="ml-2 text-gray-600">[{msg.meta.matched_documents[0].connection_type}]</span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-shield-900 border border-shield-700/50 rounded-xl px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <div className="animate-spin w-4 h-4 border-2 border-shield-accent border-t-transparent rounded-full" />
                Inspecting response for data leaks...
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-4 border-t border-shield-700/50">
        <div className="flex flex-wrap gap-2 mb-3">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => sendMessage(s)}
              className="text-xs px-3 py-1.5 rounded-full bg-shield-800 border border-shield-700 text-gray-400 hover:text-gray-200 hover:border-shield-accent/50 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex gap-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the AI assistant..."
            className="input-field flex-1"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} className="btn-primary px-4">
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
