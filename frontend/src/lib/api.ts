import { API_BASE, MUNICIPALITY } from './config';
import type { QA, QAMeta } from './types';

export interface NextQAEmpty {
  message: string;
}

export type NextQAResponse = QA | NextQAEmpty;

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${API_BASE}${path}?municipality=${encodeURIComponent(MUNICIPALITY)}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export function fetchNextQA(evaledIds: number[]): Promise<NextQAResponse> {
  return postJson<NextQAResponse>('/api/qa/next', { evaled_ids: evaledIds });
}

export function fetchMetaData(evaledIds: number[]): Promise<QAMeta[]> {
  return postJson<QAMeta[]>('/api/qa/meta', { evaled_ids: evaledIds });
}

export function isQA(value: NextQAResponse): value is QA {
  return (value as QA).QA !== undefined;
}
