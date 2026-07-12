import React, { useState, useRef, useEffect, useCallback } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import QuickActions from './QuickActions';
import { sendMessageStream, getSessionId, resetSession, getUserId, setUserId, CUSTOMERS } from '../services/api';
import './ChatPage.css';

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content: '안녕하세요! **Vroom&Dash** 고객 지원 도우미입니다.\n\n장난감 자동차에 관해 무엇이든 물어보세요! 주문 조회, 상품 추천, 기술 지원 등을 도와드릴 수 있어요.',
  timestamp: new Date(),
};

export default function ChatPage() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(getUserId());
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  const handleSend = async (text) => {
    const messageText = text || input.trim();
    if (!messageText || isLoading) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const msgId = `assistant-${Date.now()}`;

      let streamStarted = false;

      await sendMessageStream(messageText, (partialText) => {
        if (!streamStarted) {
          streamStarted = true;
          setIsLoading(false);
          setMessages((prev) => [...prev, {
            id: msgId,
            role: 'assistant',
            content: partialText,
            timestamp: new Date(),
          }]);
        } else {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === msgId ? { ...msg, content: partialText } : msg
            )
          );
        }
      });
    } catch (error) {
      console.error('[ChatPage] sendMessageStream failed:', error);
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `오류가 발생했습니다.\n\n\`\`\`\n${error.message}\n\`\`\``,
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (text) => {
    handleSend(text);
  };

  const handleReset = () => {
    if (isLoading) return;
    resetSession();
    setMessages([WELCOME_MESSAGE]);
    setInput('');
  };

  const handleUserChange = (e) => {
    if (isLoading) return;
    const id = e.target.value;
    setUserId(id);
    setCurrentUser(id);
    resetSession();
    setMessages([WELCOME_MESSAGE]);
    setInput('');
  };

  return (
    <div className="chat-page">
      {/* Header */}
      <header className="chat-header">
        <div className="header-content">
          <div className="logo-area">
            <div className="logo-icon">
              <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="20" cy="20" r="20" fill="#FF6B35"/>
                <path d="M10 24h20l-2-8H12l-2 8z" fill="white"/>
                <circle cx="14" cy="26" r="3" fill="#FFD166" stroke="white" strokeWidth="1.5"/>
                <circle cx="26" cy="26" r="3" fill="#FFD166" stroke="white" strokeWidth="1.5"/>
                <path d="M15 18l2-4h6l2 4" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="logo-text">
              <h1>Vroom&Dash</h1>
              <span className="subtitle">AI 고객 지원</span>
            </div>
          </div>
          <div className="header-right">
            <select
              className="user-select"
              value={currentUser}
              onChange={handleUserChange}
              disabled={isLoading}
            >
              {CUSTOMERS.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.id})</option>
              ))}
            </select>
            <button className="reset-button" onClick={handleReset} disabled={isLoading} title="새 대화">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
                <path d="M3 12a9 9 0 1 1 2.636 6.364" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                <path d="M3 18V12h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>새 대화</span>
            </button>
            <div className="session-badge">
              <span className="status-dot"></span>
              <span className="session-text">{getSessionId().slice(0, 12)}...</span>
            </div>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="chat-messages">
        <div className="messages-container">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Quick Actions */}
      {messages.length <= 1 && (
        <QuickActions onAction={handleQuickAction} />
      )}

      {/* Input */}
      <footer className="chat-input-area">
        <div className="input-container">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요..."
            rows={1}
            disabled={isLoading}
          />
          <button
            className={`send-button ${input.trim() && !isLoading ? 'active' : ''}`}
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        <p className="input-hint">Enter로 전송 | Shift+Enter로 줄바꿈</p>
      </footer>
    </div>
  );
}
