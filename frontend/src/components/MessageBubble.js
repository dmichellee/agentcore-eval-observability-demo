import React from 'react';
import OrderTimeline from './OrderTimeline';
import ProductCard from './ProductCard';
import './MessageBubble.css';

function parseMarkdown(text) {
  // Very lightweight markdown → HTML
  let html = text
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Strikethrough
    .replace(/~~(.*?)~~/g, '<del>$1</del>')
    // Inline code
    .replace(/`(.*?)`/g, '<code>$1</code>')
    // Line breaks
    .replace(/\n/g, '<br/>');
  return html;
}

function extractRichContent(content) {
  const rich = [];

  // Detect order status patterns
  const orderMatch = content.match(/주문번호\s*(ORD-\d+)/);
  const statusMatch = content.match(/주문 상태[：:]\s*(주문접수|결제완료|배송준비|배송중|배송완료)/);
  if (orderMatch && statusMatch) {
    rich.push({
      type: 'order_status',
      data: {
        order_id: orderMatch[1],
        status: statusMatch[1],
      },
    });
  }

  // Detect product recommendations (numbered list with PRD-xxx)
  const productMatches = [...content.matchAll(/\*\*(.*?)\*\*\s*\(PRD-(\d+)\)/g)];
  if (productMatches.length > 0) {
    const products = productMatches.map((m) => ({
      name: m[1],
      product_id: `PRD-${m[2]}`,
    }));
    rich.push({ type: 'products', data: products });
  }

  return rich;
}

function formatTime(date) {
  return new Intl.DateTimeFormat('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

export default function MessageBubble({ message }) {
  const { role, content, timestamp, isError } = message;
  const isUser = role === 'user';
  const richContent = !isUser ? extractRichContent(content) : [];

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="avatar assistant-avatar">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="16" fill="#FF6B35"/>
            <path d="M8 20h16l-1.5-6H9.5L8 20z" fill="white"/>
            <circle cx="12" cy="22" r="2" fill="#FFD166"/>
            <circle cx="20" cy="22" r="2" fill="#FFD166"/>
            <path d="M12 15l1.5-3h5l1.5 3" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
        </div>
      )}
      <div className="message-content-wrapper">
        {!isUser && <span className="sender-name">Vroom&Dash</span>}
        <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'} ${isError ? 'error-bubble' : ''}`}>
          <div
            className="message-text"
            dangerouslySetInnerHTML={{ __html: parseMarkdown(content) }}
          />
        </div>

        {/* Rich content */}
        {richContent.map((item, idx) => {
          if (item.type === 'order_status') {
            return <OrderTimeline key={idx} orderId={item.data.order_id} status={item.data.status} />;
          }
          if (item.type === 'products') {
            return (
              <div key={idx} className="product-cards-row">
                {item.data.map((p) => (
                  <ProductCard key={p.product_id} name={p.name} productId={p.product_id} />
                ))}
              </div>
            );
          }
          return null;
        })}

        <span className="message-time">{formatTime(timestamp)}</span>
      </div>
    </div>
  );
}
