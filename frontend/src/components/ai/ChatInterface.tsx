import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Sparkles, Bot } from 'lucide-react';
import { AI_CHAT_SUGGESTIONS, Product } from '../../data/mockData';
import { ProductCard } from '../ui/ProductCard';
import { chatWithAI, getCopilotAdvice, LiveProduct } from '../../services/api';
import { liveProductToCard } from '../../utils/productMapper';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  products?: Product[];
  timestamp: Date;
}

function toCards(products: LiveProduct[] | undefined): Product[] {
  if (!products || products.length === 0) return [];
  return products.slice(0, 4).map((p) => liveProductToCard(p));
}

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: "👋 Hi! I'm ShopMind AI, your intelligent shopping assistant. Ask me anything about products — I'll analyze reviews, compare specs, and find the best deals for you!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = async (text?: string) => {
    const query = text || input;
    if (!query.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const [chatResp, copilotResp] = await Promise.allSettled([
        chatWithAI(query, 6),
        getCopilotAdvice(query, 6),
      ]);

      let reply = "I couldn't generate an answer right now. Please try again.";
      let products: Product[] = [];

      if (chatResp.status === 'fulfilled') {
        reply = chatResp.value.reply || reply;
        products = toCards(chatResp.value.products as LiveProduct[] | undefined);
      }

      if (copilotResp.status === 'fulfilled') {
        const fallbackProducts = toCards(copilotResp.value.retrieved_products as LiveProduct[] | undefined);
        if (!products.length && fallbackProducts.length) products = fallbackProducts;
        if (!reply || reply.includes("couldn't")) {
          reply = copilotResp.value.advice || reply;
        }
      }

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: reply,
        products,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Backend AI is temporarily unavailable. Please verify backend server and API keys, then retry.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Messages */}
      <div style={{
        flex: 1, overflowY: 'auto', padding: '24px',
        display: 'flex', flexDirection: 'column', gap: 16,
      }}>
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              style={{
                display: 'flex',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                gap: 12,
                alignItems: 'flex-start',
              }}
            >
              {/* Avatar — sharp square, not circle */}
              <div style={{
                width: 36, height: 36,
                /* Sharp square avatar — 2px */
                borderRadius: 2,
                flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: msg.role === 'user'
                  ? '#6366F1'
                  : '#FF9900',
              }}>
                {msg.role === 'user'
                  ? <span style={{ color: 'white', fontWeight: 700, fontSize: 14 }}>U</span>
                  : <Bot size={18} color="#131A22" />
                }
              </div>

              <div style={{ maxWidth: '80%' }}>
                {/* Bubble */}
                <div
                  className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}
                  style={{ padding: '12px 16px', fontSize: 14, lineHeight: 1.7 }}
                  dangerouslySetInnerHTML={{
                    __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'),
                  }}
                />

                {/* Product cards */}
                {msg.products && msg.products.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    style={{ marginTop: 12 }}
                  >
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
                      {msg.products.map((product, i) => (
                        <ProductCard key={product.id} product={product} index={i} />
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}
            >
              <div style={{
                width: 36, height: 36,
                /* Sharp — 2px */
                borderRadius: 2,
                flexShrink: 0,
                background: '#FF9900',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Bot size={18} color="#131A22" />
              </div>
              <div className="chat-bubble-ai" style={{ padding: '14px 18px', display: 'flex', gap: 6, alignItems: 'center' }}>
                <div className="chat-typing-dot" />
                <div className="chat-typing-dot" />
                <div className="chat-typing-dot" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      <div style={{ padding: '0 24px 12px', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {AI_CHAT_SUGGESTIONS.slice(0, 3).map((suggestion, i) => (
          <motion.button
            key={i}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => sendMessage(suggestion)}
            style={{
              padding: '5px 12px',
              background: 'rgba(255,153,0,0.06)',
              border: '1px solid rgba(255,153,0,0.18)',
              /* SHARP — not pill */
              borderRadius: 2,
              color: '#FF9900',
              fontSize: 11, fontWeight: 700, cursor: 'pointer',
              whiteSpace: 'nowrap',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              fontFamily: 'JetBrains Mono, monospace',
            }}
          >
            {suggestion}
          </motion.button>
        ))}
      </div>

      {/* Input */}
      <div style={{
        padding: '12px 24px 24px',
        borderTop: '1px solid var(--border-color)',
      }}>
        <div style={{
          display: 'flex', gap: 0, alignItems: 'center',
          background: 'var(--bg-card)',
          border: '1.5px solid var(--border-color)',
          /* SHARP rectangular input — not pill */
          borderRadius: 2,
          overflow: 'hidden',
          transition: 'border-color 0.15s',
        }}
          onFocus={() => {}}
        >
          <div style={{ padding: '10px 12px', borderRight: '1px solid var(--border-color)', display: 'flex', alignItems: 'center' }}>
            <Sparkles size={15} color="#FF9900" />
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about any product..."
            style={{
              flex: 1, background: 'transparent', border: 'none',
              color: 'var(--text-primary)', fontSize: 14, outline: 'none',
              padding: '10px 12px',
            }}
          />
          <motion.button
            whileHover={{ scale: 1.0 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => sendMessage()}
            disabled={!input.trim()}
            style={{
              width: 44, height: 44,
              /* Sharp send button — 0px */
              borderRadius: 0,
              background: input.trim() ? '#FF9900' : 'rgba(255,255,255,0.04)',
              border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: input.trim() ? 'pointer' : 'default',
              transition: 'background 0.15s',
              flexShrink: 0,
            }}
          >
            <Send size={15} color={input.trim() ? '#0D1117' : 'rgba(255,255,255,0.25)'} />
          </motion.button>
        </div>
      </div>
    </div>
  );
};
