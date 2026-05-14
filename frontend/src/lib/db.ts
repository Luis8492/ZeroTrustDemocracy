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
const DB_VERSION = 3;

let dbPromise: Promise<IDBPDatabase<ZTDDB>> | null = null;

export function getDB(): Promise<IDBPDatabase<ZTDDB>> {
  if (!dbPromise) {
    dbPromise = openDB<ZTDDB>(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion) {
        if (oldVersion < 1) {
          db.createObjectStore('evaluations', { keyPath: 'QA_id' });
        }
        if (oldVersion < 2) {
          db.createObjectStore('settings');
        }
        if (oldVersion >= 1 && oldVersion < 3) {
          // Schema change: importance を追加。旧データは破棄する。
          db.deleteObjectStore('evaluations');
          db.createObjectStore('evaluations', { keyPath: 'QA_id' });
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
