import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader } from 'lucide-react';
import { getCopilotAdvice } from '../services/api';
import { ProductCard } from '../components/ui/ProductCard';
import '../styles/copilot.css';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  products?: any[];
}

export const CopilotPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content:
        "Hi! I'm ShopMind AI, your personal shopping assistant. I can help you find products, compare items, understand reviews, and provide shopping advice. What are you looking for today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    // Get bot response
    setIsLoading(true);
    try {
      const response = await getCopilotAdvice(input);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.advice,
        timestamp: new Date(),
        products: response.retrieved_products,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content:
          "I'm having trouble connecting to the service. Please make sure the backend API is running on localhost:8000. Try asking: 'Best laptop under 50000'",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="copilot-page">
      <div className="copilot-container">
        <div className="copilot-header">
          <h1>ShopMind AI Assistant</h1>
          <p>Your intelligent shopping companion</p>
        </div>

        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'bot' ? (
                  <Bot size={20} />
                ) : (
                  <User size={20} />
                )}
              </div>
              <div className="message-content">
                <p>{message.content}</p>
                {message.products && message.products.length > 0 && (
                  <div className="products-preview">
                    <h4>Related Products:</h4>
                    <div className="products-grid">
                      {message.products.map((product) => (
                        <ProductCard
                          key={product.product_id}
                          product={product}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message bot">
              <div className="message-avatar">
                <Bot size={20} />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSendMessage} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me about products, comparisons, reviews, or shopping advice..."
            disabled={isLoading}
            className="message-input"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="send-button"
          >
            {isLoading ? <Loader size={20} /> : <Send size={20} />}
          </button>
        </form>

        <div className="suggestions">
          <p className="suggestions-title">Try asking:</p>
          <div className="suggestion-buttons">
            <button
              onClick={() => setInput('Best laptop for machine learning under 50000')}
              className="suggestion-btn"
            >
              "Best laptop for ML under ₹50000"
            </button>
            <button
              onClick={() => setInput('Compare iPhone and Samsung phones')}
              className="suggestion-btn"
            >
              "Compare iPhone and Samsung"
            </button>
            <button
              onClick={() => setInput('What are the best headphones for music')}
              className="suggestion-btn"
            >
              "Best headphones for music"
            </button>
            <button
              onClick={() => setInput('Show me trending products')}
              className="suggestion-btn"
            >
              "Show trending products"
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
