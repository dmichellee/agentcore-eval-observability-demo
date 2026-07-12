import React from 'react';
import './QuickActions.css';

const ACTIONS = [
  { icon: '📦', label: '주문 조회', text: '주문번호 ORD-002 조회해줘' },
  { icon: '🚗', label: '상품 추천', text: '5살 아이한테 맞는 RC카 추천해줘' },
  { icon: '🔧', label: '기술 지원', text: 'RC카 리모컨이 연결이 안 돼요' },
  { icon: '🔄', label: '반품 문의', text: '주문번호 ORD-001 반품 요청하고 싶어요' },
];

export default function QuickActions({ onAction }) {
  return (
    <div className="quick-actions">
      <p className="quick-actions-title">이런 것도 물어볼 수 있어요</p>
      <div className="quick-actions-grid">
        {ACTIONS.map((action) => (
          <button
            key={action.label}
            className="quick-action-btn"
            onClick={() => onAction(action.text)}
          >
            <span className="quick-action-icon">{action.icon}</span>
            <span className="quick-action-label">{action.label}</span>
            <span className="quick-action-example">{action.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
