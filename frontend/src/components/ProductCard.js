import React from 'react';
import './ProductCard.css';

// Color mapping for product categories
const CATEGORY_COLORS = {
  'RC카': '#FF6B35',
  '미니카': '#4ECDC4',
  '조립키트': '#FFD166',
  '트랙세트': '#7B68EE',
};

export default function ProductCard({ name, productId }) {
  const categoryGuess = name.includes('RC') || name.includes('rc')
    ? 'RC카'
    : name.includes('미니카') || name.includes('컬렉션')
    ? '미니카'
    : name.includes('조립') || name.includes('키트')
    ? '조립키트'
    : '트랙세트';

  const color = CATEGORY_COLORS[categoryGuess] || '#FF6B35';

  return (
    <div className="product-card" style={{ borderTopColor: color }}>
      <div className="product-card-icon" style={{ background: `${color}15` }}>
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="4" y="12" width="24" height="10" rx="3" fill={color} opacity="0.8"/>
          <circle cx="10" cy="24" r="3" fill={color}/>
          <circle cx="22" cy="24" r="3" fill={color}/>
          <path d="M8 12l3-5h10l3 5" fill={color} opacity="0.6"/>
        </svg>
      </div>
      <div className="product-card-info">
        <span className="product-card-name">{name}</span>
        <span className="product-card-id">{productId}</span>
      </div>
      <span className="product-card-badge" style={{ background: `${color}20`, color }}>{categoryGuess}</span>
    </div>
  );
}
