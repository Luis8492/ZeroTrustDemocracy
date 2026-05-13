export interface Speech {
  mark: string;
  role: string;
  comment: string;
  name?: string;
}

export interface QA {
  id: number;
  uuid: string;
  committee_date: string;
  committee_name: string;
  topic_intro: Speech[];
  QA: Speech[];
  eval_target: string;
}

export interface QAMeta {
  id: number;
  uuid: string;
  questioner: string;
  questioner_party: string;
  committee_date: string;
  committee_name: string;
  topic_intro: Speech[];
  QA: Speech[];
}

export interface EvaluationRecord {
  QA_id: number;
  eval: number;
  importance: number;
}

export type ThemeName = 'plain' | 'chat' | 'scroll' | 'hud';
