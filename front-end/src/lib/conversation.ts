/** The current conversation and its result. All numbers come from the API; none are computed here. */
import { create } from 'zustand';

import { api, errorMessage } from './api';
import type { Assessment, AssessmentDetail, Message, Profile, Turn } from './types';

type ConversationState = {
  id: number | null;
  messages: Message[];
  profile: Profile | null;
  assessment: Assessment | null;
  preview: Assessment | null;
  busy: boolean;
  error: string | null;
  start: () => Promise<void>;
  send: (text: string) => Promise<void>;
  open: (id: number) => Promise<void>;
  whatIf: (changes: Profile) => Promise<void>;
  clearPreview: () => void;
  reset: () => void;
};

const EMPTY = { id: null, messages: [], profile: null, assessment: null, preview: null, busy: false, error: null };

export const useConversation = create<ConversationState>((set, get) => {
  const run = async (work: () => Promise<void>) => {
    set({ busy: true, error: null });
    try {
      await work();
    } catch (error) {
      set({ error: errorMessage(error) });
    } finally {
      set({ busy: false });
    }
  };

  const applyTurn = (turn: Turn) =>
    set((state) => ({
      id: turn.id,
      profile: turn.profile,
      assessment: turn.assessment,
      preview: null,
      messages: [...state.messages, { role: 'assistant', text: turn.reply }],
    }));

  return {
    ...EMPTY,

    start: () =>
      run(async () => {
        set({ ...EMPTY, busy: true });
        applyTurn(await api<Turn>('/assessments', { body: {} }));
      }),

    send: (text) =>
      run(async () => {
        const { id } = get();
        if (id === null) return;
        set((state) => ({ messages: [...state.messages, { role: 'user', text }] }));
        applyTurn(await api<Turn>(`/assessments/${id}/chat`, { body: { message: text } }));
      }),

    open: (id) =>
      run(async () => {
        const detail = await api<AssessmentDetail>(`/assessments/${id}`);
        set({ id, messages: detail.messages, profile: detail.profile, assessment: detail.assessment, preview: null });
      }),

    whatIf: (changes) =>
      run(async () => {
        const profile = { ...get().profile, ...changes };
        set({ preview: await api<Assessment>('/calculator/assess', { body: { profile } }) });
      }),

    clearPreview: () => set({ preview: null }),
    reset: () => set(EMPTY),
  };
});
