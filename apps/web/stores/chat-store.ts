import { create } from "zustand";

import {
  getRagSourcesFromMessageRead,
  getToolStepsFromMessageRead,
  type MessageRead,
  type RagSourceItem,
  type ToolStepItem,
} from "@/lib/chat-types";

type RagSourcesState = {
  /** Sources for the in-flight assistant turn (before message id is known). */
  streamingRagSources: RagSourceItem[] | null;
  /** Persisted or finalized sources keyed by assistant message id. */
  ragSourcesByMessageId: Record<string, RagSourceItem[]>;
};

type ToolStepsState = {
  /** Tool rounds for the in-flight assistant turn (before message id is known). */
  streamingToolSteps: ToolStepItem[] | null;
  /** Persisted or finalized tool steps keyed by assistant message id. */
  toolStepsByMessageId: Record<string, ToolStepItem[]>;
};

type ChatStoreState = RagSourcesState &
  ToolStepsState & {
    input: string;
    error: string | null;
    bootstrapping: boolean;
    syncedFingerprint: string;
  };

type ChatStoreActions = {
  setInput: (input: string) => void;
  setError: (error: string | null) => void;
  setBootstrapping: (bootstrapping: boolean) => void;
  resetConversationSync: () => void;
  /** Clear sync fingerprint only — keeps rag/tool auxiliary state during in-flight persist fetch. */
  resetPersistedSyncFingerprint: () => void;
  shouldSyncPersistedMessages: (fingerprint: string) => boolean;
  markPersistedMessagesSynced: (fingerprint: string) => void;
  prepareSend: () => void;
  resetRagSources: () => void;
  setStreamingRagSources: (items: RagSourceItem[] | null) => void;
  commitStreamingRagSources: (messageId: string) => void;
  setRagSourcesForMessage: (
    messageId: string,
    items: RagSourceItem[] | null,
  ) => void;
  hydrateHistoryRagSources: (rows: MessageRead[]) => void;
  getRagSourcesForMessage: (
    messageId: string | undefined,
    isStreaming: boolean,
  ) => RagSourceItem[] | null;
  resetToolSteps: () => void;
  setStreamingToolSteps: (items: ToolStepItem[] | null) => void;
  commitStreamingToolSteps: (messageId: string) => void;
  setToolStepsForMessage: (
    messageId: string,
    items: ToolStepItem[] | null,
  ) => void;
  hydrateHistoryToolSteps: (rows: MessageRead[]) => void;
  getToolStepsForMessage: (
    messageId: string | undefined,
    isStreaming: boolean,
  ) => ToolStepItem[] | null;
};

export type ChatStore = ChatStoreState & ChatStoreActions;

const emptyRagSourcesState = (): RagSourcesState => ({
  streamingRagSources: null,
  ragSourcesByMessageId: {},
});

const emptyToolStepsState = (): ToolStepsState => ({
  streamingToolSteps: null,
  toolStepsByMessageId: {},
});

export const useChatStore = create<ChatStore>((set, get) => ({
  ...emptyRagSourcesState(),
  ...emptyToolStepsState(),
  input: "",
  error: null,
  bootstrapping: false,
  syncedFingerprint: "",

  setInput: (input) => set({ input }),

  setError: (error) => set({ error }),

  setBootstrapping: (bootstrapping) => set({ bootstrapping }),

  resetConversationSync: () =>
    set({
      syncedFingerprint: "",
      ...emptyRagSourcesState(),
      ...emptyToolStepsState(),
    }),

  resetPersistedSyncFingerprint: () => set({ syncedFingerprint: "" }),

  shouldSyncPersistedMessages: (fingerprint) =>
    get().syncedFingerprint !== fingerprint,

  markPersistedMessagesSynced: (fingerprint) =>
    set({ syncedFingerprint: fingerprint }),

  prepareSend: () =>
    set({
      input: "",
      error: null,
      streamingRagSources: null,
      streamingToolSteps: null,
    }),

  resetRagSources: () => set(emptyRagSourcesState()),

  setStreamingRagSources: (items) => set({ streamingRagSources: items }),

  commitStreamingRagSources: (messageId) => {
    const { streamingRagSources, ragSourcesByMessageId } = get();
    if (!streamingRagSources?.length) {
      set({ streamingRagSources: null });
      return;
    }
    set({
      ragSourcesByMessageId: {
        ...ragSourcesByMessageId,
        [messageId]: streamingRagSources,
      },
      streamingRagSources: null,
    });
  },

  setRagSourcesForMessage: (messageId, items) =>
    set((state) => {
      if (!items?.length) {
        const next = { ...state.ragSourcesByMessageId };
        delete next[messageId];
        return { ragSourcesByMessageId: next };
      }
      return {
        ragSourcesByMessageId: {
          ...state.ragSourcesByMessageId,
          [messageId]: items,
        },
      };
    }),

  hydrateHistoryRagSources: (rows) => {
    const ragSourcesByMessageId: Record<string, RagSourceItem[]> = {};
    for (const row of rows) {
      if (row.role !== "assistant") {
        continue;
      }
      const sources = getRagSourcesFromMessageRead(row);
      if (sources) {
        ragSourcesByMessageId[row.id] = sources;
      }
    }
    set({ ragSourcesByMessageId });
  },

  getRagSourcesForMessage: (messageId, isStreaming) => {
    const state = get();
    if (isStreaming && state.streamingRagSources?.length) {
      return state.streamingRagSources;
    }
    if (messageId && state.ragSourcesByMessageId[messageId]) {
      return state.ragSourcesByMessageId[messageId];
    }
    return null;
  },

  resetToolSteps: () => set(emptyToolStepsState()),

  setStreamingToolSteps: (items) => set({ streamingToolSteps: items }),

  commitStreamingToolSteps: (messageId) => {
    const { streamingToolSteps, toolStepsByMessageId } = get();
    if (!streamingToolSteps?.length) {
      set({ streamingToolSteps: null });
      return;
    }
    set({
      toolStepsByMessageId: {
        ...toolStepsByMessageId,
        [messageId]: streamingToolSteps,
      },
      streamingToolSteps: null,
    });
  },

  setToolStepsForMessage: (messageId, items) =>
    set((state) => {
      if (!items?.length) {
        const next = { ...state.toolStepsByMessageId };
        delete next[messageId];
        return { toolStepsByMessageId: next };
      }
      return {
        toolStepsByMessageId: {
          ...state.toolStepsByMessageId,
          [messageId]: items,
        },
      };
    }),

  hydrateHistoryToolSteps: (rows) => {
    const toolStepsByMessageId: Record<string, ToolStepItem[]> = {};
    for (const row of rows) {
      if (row.role !== "assistant") {
        continue;
      }
      const steps = getToolStepsFromMessageRead(row);
      if (steps) {
        toolStepsByMessageId[row.id] = steps;
      }
    }
    set({ toolStepsByMessageId });
  },

  getToolStepsForMessage: (messageId, isStreaming) => {
    const state = get();
    if (isStreaming && state.streamingToolSteps?.length) {
      return state.streamingToolSteps;
    }
    if (messageId && state.toolStepsByMessageId[messageId]) {
      return state.toolStepsByMessageId[messageId];
    }
    return null;
  },
}));
