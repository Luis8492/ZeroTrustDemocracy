import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { EvaluationRecord, ThemeName } from './types';

interface ZTDDB extends DBSchema {
  evaluations: {
    key: number;
    value: EvaluationRecord;
  };
  settings: {
    key: string;
    value: unknown;
  };
}

const DB_NAME = 'EvalDB';
// v4: 過去のアップグレード途中の壊れた DB を回復させるため、
// 「必要なストアを冪等に揃える」処理に切り替えた。
const DB_VERSION = 4;

let dbPromise: Promise<IDBPDatabase<ZTDDB>> | null = null;

export function getDB(): Promise<IDBPDatabase<ZTDDB>> {
  if (!dbPromise) {
    dbPromise = openDB<ZTDDB>(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion) {
        // v3 でスキーマ変更（importance 追加）。v1〜v2 からの移行時のみ
        // 旧データを破棄する。store が無いケースもあるので存在チェック。
        if (
          oldVersion >= 1 &&
          oldVersion < 3 &&
          db.objectStoreNames.contains('evaluations')
        ) {
          db.deleteObjectStore('evaluations');
        }
        // 必須ストアを冪等に作成（途中で壊れた DB も自己修復する）。
        if (!db.objectStoreNames.contains('evaluations')) {
          db.createObjectStore('evaluations', { keyPath: 'QA_id' });
        }
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings');
        }
      },
    });
  }
  return dbPromise;
}

export async function saveEvaluation(record: EvaluationRecord): Promise<void> {
  const db = await getDB();
  await db.put('evaluations', record);
}

export async function listEvaluatedIDs(): Promise<number[]> {
  const db = await getDB();
  const all = await db.getAll('evaluations');
  return all.map((e) => e.QA_id);
}

export async function listEvaluations(): Promise<EvaluationRecord[]> {
  const db = await getDB();
  return db.getAll('evaluations');
}

export async function countEvaluations(): Promise<number> {
  const db = await getDB();
  return db.count('evaluations');
}

export async function clearEvaluations(): Promise<void> {
  const db = await getDB();
  await db.clear('evaluations');
}

export async function getSetting<T>(key: string, fallback: T): Promise<T> {
  const db = await getDB();
  const value = await db.get('settings', key);
  return (value as T) ?? fallback;
}

export async function setSetting(key: string, value: unknown): Promise<void> {
  const db = await getDB();
  await db.put('settings', value, key);
}

export async function getTheme(): Promise<ThemeName> {
  return getSetting<ThemeName>('theme', 'plain');
}

export async function setTheme(theme: ThemeName): Promise<void> {
  await setSetting('theme', theme);
}

export async function getOnboardingCompleted(): Promise<boolean> {
  return getSetting<boolean>('onboarding_completed', false);
}

export async function setOnboardingCompleted(value: boolean): Promise<void> {
  await setSetting('onboarding_completed', value);
}
