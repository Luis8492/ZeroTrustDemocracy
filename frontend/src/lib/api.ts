import { DATA_BASE } from './config';
import type { QA, QAMeta, Speech } from './types';

export interface NextQAEmpty {
  message: string;
}

export type NextQAResponse = QA | NextQAEmpty;

interface IndexEntry {
  id: number;
  uuid: string;
  questioner: string;
  questioner_party: string;
  file_name: string;
  committee_date: string;
  committee_name: string;
}

interface IndexFile {
  municipality: string;
  generated_at: string;
  qa_count: number;
  meeting_count: number;
  qas: IndexEntry[];
}

interface MeetingQA {
  id: number;
  uuid: string;
  questioner: string;
  questioner_party: string;
  topic_intro: Speech[];
  QA: Speech[];
  eval_target: string;
}

interface MeetingFile {
  file_name: string;
  committee_date: string;
  committee_name: string;
  qas: MeetingQA[];
}

let indexPromise: Promise<IndexFile> | null = null;
const meetingCache = new Map<string, Promise<MeetingFile>>();

async function getIndex(): Promise<IndexFile> {
  if (!indexPromise) {
    indexPromise = fetchJson<IndexFile>(`${DATA_BASE}/index.json`);
  }
  return indexPromise;
}

async function getMeeting(fileName: string): Promise<MeetingFile> {
  let cached = meetingCache.get(fileName);
  if (!cached) {
    cached = fetchJson<MeetingFile>(
      `${DATA_BASE}/meetings/${encodeURIComponent(fileName)}.json`,
    );
    meetingCache.set(fileName, cached);
  }
  return cached;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status}`);
  return (await res.json()) as T;
}

function weightedPick<T>(items: T[], weights: number[]): T {
  const total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (let i = 0; i < items.length; i++) {
    r -= weights[i];
    if (r <= 0) return items[i];
  }
  return items[items.length - 1];
}

export async function fetchNextQA(evaledIds: number[]): Promise<NextQAResponse> {
  const idx = await getIndex();
  const evaledSet = new Set(evaledIds);

  const candidates = idx.qas.filter((q) => !evaledSet.has(q.id));
  if (!candidates.length) return { message: '全て評価済みです' };

  const evaledCounts = new Map<string, number>();
  for (const q of idx.qas) {
    if (evaledSet.has(q.id)) {
      evaledCounts.set(q.questioner, (evaledCounts.get(q.questioner) ?? 0) + 1);
    }
  }
  const weights = candidates.map((q) => 1 / ((evaledCounts.get(q.questioner) ?? 0) + 1));
  const pick = weightedPick(candidates, weights);

  const meeting = await getMeeting(pick.file_name);
  const qa = meeting.qas.find((q) => q.id === pick.id);
  if (!qa) throw new Error(`QA ${pick.id} missing in meeting ${pick.file_name}`);

  return {
    id: qa.id,
    uuid: qa.uuid,
    committee_date: meeting.committee_date,
    committee_name: meeting.committee_name,
    topic_intro: qa.topic_intro,
    QA: qa.QA,
    questioner: qa.questioner,
    questioner_party: qa.questioner_party,
    eval_target: qa.eval_target,
  };
}

export async function fetchMetaData(evaledIds: number[]): Promise<QAMeta[]> {
  if (!evaledIds.length) return [];
  const idx = await getIndex();
  const byId = new Map(idx.qas.map((q) => [q.id, q]));
  const targets = evaledIds
    .map((id) => byId.get(id))
    .filter((q): q is IndexEntry => Boolean(q));

  const uniqueFiles = [...new Set(targets.map((q) => q.file_name))];
  const meetings = await Promise.all(uniqueFiles.map(getMeeting));
  const byFile = new Map(meetings.map((m) => [m.file_name, m]));

  const result: QAMeta[] = [];
  for (const t of targets) {
    const meeting = byFile.get(t.file_name);
    if (!meeting) continue;
    const qa = meeting.qas.find((q) => q.id === t.id);
    if (!qa) continue;
    result.push({
      id: qa.id,
      uuid: qa.uuid,
      questioner: qa.questioner,
      questioner_party: qa.questioner_party,
      topic_intro: qa.topic_intro,
      QA: qa.QA,
      committee_date: meeting.committee_date,
      committee_name: meeting.committee_name,
    });
  }
  return result;
}

export function isQA(value: NextQAResponse): value is QA {
  return (value as QA).QA !== undefined;
}
