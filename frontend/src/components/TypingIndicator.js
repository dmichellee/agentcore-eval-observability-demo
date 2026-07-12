import React from 'react';
import './TypingIndicator.css';

export default function TypingIndicator() {
  return (
    <div className="message-row assistant">
      <div className="avatar assistant-avatar">
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="16" cy="16" r="16" fill="#FF6B35"/>
          <path d="M8 20h16l-1.5-6H9.5L8 20z" fill="white"/>
          <circle cx="12" cy="22" r="2" fill="#FFD166"/>
          <circle cx="20" cy="22" r="2" fill="#FFD166"/>
          <path d="M12 15l1.5-3h5l1.5 3" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
        </svg>
      </div>
      <div className="message-content-wrapper">
        <span className="sender-name">Vroom&Dash</span>
        <div className="typing-bubble">
          <div className="typing-dots">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        </div>
      </div>
    </div>
  );
}
