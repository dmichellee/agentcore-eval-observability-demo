import React from 'react';
import './OrderTimeline.css';

const STEPS = ['주문접수', '결제완료', '배송준비', '배송중', '배송완료'];

export default function OrderTimeline({ orderId, status }) {
  const currentIdx = STEPS.indexOf(status);

  return (
    <div className="order-timeline">
      <div className="timeline-header">
        <span className="timeline-label">주문 진행 상태</span>
        <span className="timeline-order-id">{orderId}</span>
      </div>
      <div className="timeline-steps">
        {STEPS.map((step, idx) => {
          const isDone = idx <= currentIdx;
          const isCurrent = idx === currentIdx;
          return (
            <div key={step} className={`timeline-step ${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}`}>
              <div className="step-dot">
                {isDone && (
                  <svg viewBox="0 0 16 16" fill="none">
                    <path d="M4 8l3 3 5-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </div>
              {idx < STEPS.length - 1 && <div className={`step-line ${idx < currentIdx ? 'done' : ''}`} />}
              <span className="step-label">{step}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
