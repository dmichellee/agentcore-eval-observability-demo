import { HttpRequest } from '@aws-sdk/protocol-http';
import { SignatureV4 } from '@aws-sdk/signature-v4';
import { Sha256 } from '@aws-crypto/sha256-browser';
import { getAwsCredentials, getRegion } from './auth';

// Written to frontend/.env.local by scripts/10-write-frontend-env.sh.
const RUNTIME_ARN = process.env.REACT_APP_AGENTCORE_RUNTIME_ARN || '';

const REGION = getRegion();
const SERVICE = 'bedrock-agentcore';
const HOST = `bedrock-agentcore.${REGION}.amazonaws.com`;
const ENCODED_ARN = encodeURIComponent(RUNTIME_ARN);
const PATH = `/runtimes/${ENCODED_ARN}/invocations`;

function generateSessionId() {
  const seg = () => Math.random().toString(36).substring(2, 10);
  return `sess_${seg()}-${seg()}-${seg()}-${seg()}`;
}

let sessionId = localStorage.getItem('vroom_session_id');
if (!sessionId || sessionId.length < 33) {
  sessionId = generateSessionId();
  localStorage.setItem('vroom_session_id', sessionId);
}

let userId = localStorage.getItem('vroom_user_id') || 'CUST-001';

export const CUSTOMERS = [
  { id: 'CUST-001', name: '김민준' },
  { id: 'CUST-002', name: '이서연' },
  { id: 'CUST-003', name: '박지호' },
];

export function getSessionId() {
  return sessionId;
}

export function getUserId() {
  return userId;
}

export function setUserId(id) {
  userId = id;
  localStorage.setItem('vroom_user_id', id);
}

export function resetSession() {
  sessionId = generateSessionId();
  localStorage.setItem('vroom_session_id', sessionId);
  return sessionId;
}

async function signRequest(method, path, headers, body) {
  const credentials = await getAwsCredentials();

  const request = new HttpRequest({
    method,
    protocol: 'https:',
    hostname: HOST,
    path,
    headers: {
      host: HOST,
      ...headers,
    },
    body,
  });

  const signer = new SignatureV4({
    credentials,
    region: REGION,
    service: SERVICE,
    sha256: Sha256,
  });

  return signer.sign(request);
}

function parseSSEResponse(raw) {
  let result = '';
  for (const line of raw.split('\n')) {
    if (!line.startsWith('data: ')) continue;
    const payload = line.slice(6);
    if (payload === '[DONE]') break;
    try {
      const parsed = JSON.parse(payload);
      if (typeof parsed === 'string') { result += parsed; continue; }
      if (parsed.response) { result += parsed.response; continue; }
      if (parsed.output) { result += typeof parsed.output === 'string' ? parsed.output : JSON.stringify(parsed.output); continue; }
      if (parsed.delta?.text) { result += parsed.delta.text; continue; }
      result += JSON.stringify(parsed);
    } catch {
      // plain text chunk (not JSON-wrapped)
      result += payload;
    }
  }
  return result;
}

export async function sendMessage(message) {
  const body = JSON.stringify({ prompt: message, user_id: userId });

  const signed = await signRequest('POST', PATH, {
    'Content-Type': 'application/json',
    'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
  }, body);

  const response = await fetch(`https://${HOST}${PATH}`, {
    method: 'POST',
    headers: signed.headers,
    body,
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('AgentCore error:', response.status, errorText);
    throw new Error(`AgentCore error: ${response.status}`);
  }

  const raw = await response.text();

  // SSE streaming format (data: ...)
  if (raw.startsWith('data: ')) {
    return parseSSEResponse(raw).trimStart();
  }

  // Plain JSON
  try {
    const data = JSON.parse(raw);
    if (typeof data === 'string') return data;
    if (data.response) return data.response;
    if (data.output) return typeof data.output === 'string' ? data.output : JSON.stringify(data.output);
    if (data.result) return typeof data.result === 'string' ? data.result : JSON.stringify(data.result);
    return JSON.stringify(data);
  } catch {
    return raw;
  }
}

export async function sendMessageStream(message, onChunk) {
  const body = JSON.stringify({ prompt: message, user_id: userId });

  const signed = await signRequest('POST', PATH, {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
    'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
  }, body);

  const response = await fetch(`https://${HOST}${PATH}`, {
    method: 'POST',
    headers: signed.headers,
    body,
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('AgentCore stream error:', response.status, errorText);
    throw new Error(`AgentCore error: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE lines from buffer
    const lines = buffer.split('\n');
    buffer = lines.pop(); // keep incomplete last line in buffer

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const payload = line.slice(6);
      if (payload === '[DONE]') continue;
      try {
        const parsed = JSON.parse(payload);
        if (typeof parsed === 'string') { fullText += parsed; }
        else if (parsed.response) { fullText += parsed.response; }
        else if (parsed.delta?.text) { fullText += parsed.delta.text; }
        else if (parsed.output) { fullText += typeof parsed.output === 'string' ? parsed.output : JSON.stringify(parsed.output); }
        else { fullText += JSON.stringify(parsed); }
      } catch {
        fullText += payload;
      }
      onChunk(fullText.trimStart());
    }
  }

  // Process any remaining buffer
  if (buffer.startsWith('data: ')) {
    const payload = buffer.slice(6);
    if (payload && payload !== '[DONE]') {
      try {
        const parsed = JSON.parse(payload);
        if (typeof parsed === 'string') { fullText += parsed; }
        else if (parsed.response) { fullText += parsed.response; }
        else if (parsed.delta?.text) { fullText += parsed.delta.text; }
        else { fullText += JSON.stringify(parsed); }
      } catch {
        fullText += payload;
      }
      onChunk(fullText.trimStart());
    }
  }

  return fullText.trimStart();
}

// Demo mode: simulate agent responses locally for demo/development
const DEMO_RESPONSES = {
  order: (id) => `주문번호 ${id}을 확인했습니다.\n\n**주문 상태**: 배송중\n**상품**: 스피드 레이서 RC카\n**결제 금액**: 40,500원\n**택배사**: CJ대한통운\n**예상 도착일**: 2025-04-05\n\n현재 서울 송파 허브터미널을 통과했습니다. 곧 배송될 예정이에요!`,
  recommend: `5세 아이에게 적합한 상품을 추천드립니다!\n\n1. **미니 레이싱 RC카 세트** (PRD-004)\n   - 가격: ~~35,000원~~ → 28,000원 (20% 할인)\n   - 권장 연령: 5세 이상\n   - 간단한 조작, 2대 세트로 친구와 함께!\n\n2. **공룡 RC카** (PRD-007)\n   - 가격: ~~52,000원~~ → 46,800원 (10% 할인)\n   - 권장 연령: 5세 이상\n   - 공룡 모양 + 소리/빛 효과!\n\n3. **고무동력 자동차 조립키트** (PRD-023)\n   - 가격: 12,000원\n   - 권장 연령: 5세 이상\n   - 배터리 없이 고무줄로 달려요!`,
  tech: `리모컨 페어링 방법을 안내드립니다.\n\n**2.4GHz 리모컨 페어링 순서:**\n\n1. RC카와 리모컨의 전원을 모두 끕니다.\n2. RC카의 전원을 먼저 켭니다.\n3. 3초 이내에 리모컨의 전원을 켭니다.\n4. 리모컨의 트리거를 한 번 당겼다 놓으세요.\n5. LED가 깜빡임 → 점등으로 바뀌면 페어링 성공!\n\n그래도 안 되면 주변의 다른 2.4GHz 기기를 끄고 다시 시도해보세요.`,
  default: `안녕하세요! 무엇을 도와드릴까요?\n\n다음과 같은 것들을 도와드릴 수 있어요:\n- 주문/배송 조회\n- 상품 검색 및 추천\n- 기술 지원 (조립, 고장, 배터리, 리모컨)\n- 반품/교환 요청`,
};

export async function sendMessageDemo(message) {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));

  const msg = message.toLowerCase();
  if (msg.includes('ord-') || msg.includes('주문') || msg.includes('배송')) {
    const ordMatch = message.match(/ORD-\d+/i);
    return DEMO_RESPONSES.order(ordMatch ? ordMatch[0].toUpperCase() : 'ORD-001');
  }
  if (msg.includes('추천') || msg.includes('살') || msg.includes('세')) {
    return DEMO_RESPONSES.recommend;
  }
  if (msg.includes('리모컨') || msg.includes('페어링') || msg.includes('고장') || msg.includes('배터리') || msg.includes('조립')) {
    return DEMO_RESPONSES.tech;
  }
  return DEMO_RESPONSES.default;
}
