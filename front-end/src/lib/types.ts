/** Shapes returned by the API. Source of truth: docs/api.md. */

export type User = { id: number; email: string; name: string };
export type Session = { token: string; user: User };

export type Line = {
  key: string;
  label: string;
  amount: number;
  reason: string;
};
export type Assumption = {
  key: string;
  label: string;
  value: number;
  source: string;
  url: string | null;
  as_of: string | null;
};
export type Option = { what: string; fits_when: string[]; tradeoffs: string[] };

export type Assessment = {
  total_need: number;
  resources: number;
  gap: number;
  fully_covered: boolean;
  components: Line[];
  offsets: Line[];
  assumptions: Assumption[];
  method: string;
  projection: {
    years: { year: number; remaining_need: number }[];
    covered_year: number | null;
    suggested_term_years: number | null;
    reason: string;
  };
  comparison: { term: Option; permanent: Option; note: string };
};

export type Profile = {
  annual_income?: number;
  income_years_to_replace?: number;
  fund_education?: boolean;
  [field: string]: unknown;
};

export type Message = { role: "user" | "assistant"; text: string };
export type Turn = {
  id: number;
  reply: string;
  profile: Profile | null;
  assessment: Assessment | null;
  done: boolean;
};
export type AssessmentDetail = Omit<Turn, "reply"> & {
  created_at: string;
  messages: Message[];
};
export type AssessmentSummary = {
  id: number;
  created_at: string;
  done: boolean;
  total_need: number | null;
  gap: number | null;
};
