import { create } from "zustand";

type ChatStoreState = {
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
  shouldSyncPersistedMessages: (fingerprint: string) => boolean;
  markPersistedMessagesSynced: (fingerprint: string) => void;
  prepareSend: () => void;
};

export type ChatStore = ChatStoreState & ChatStoreActions;

export const useChatStore = create<ChatStore>((set, get) => ({
  input: "",
  error: null,
  bootstrapping: false,
  syncedFingerprint: "",

  setInput: (input) => set({ input }),

  setError: (error) => set({ error }),

  setBootstrapping: (bootstrapping) => set({ bootstrapping }),

  resetConversationSync: () => set({ syncedFingerprint: "" }),

  shouldSyncPersistedMessages: (fingerprint) =>
    get().syncedFingerprint !== fingerprint,

  markPersistedMessagesSynced: (fingerprint) =>
    set({ syncedFingerprint: fingerprint }),

  prepareSend: () => set({ input: "", error: null }),
}));
