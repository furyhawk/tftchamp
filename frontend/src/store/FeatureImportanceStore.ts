import create from 'zustand';

type Payload = {
    label: string;
    feature_importance: number;
}

type State = {
    payload: Array<Payload> | null;

    setPayload: (payload: Array<Payload> | null) => void;
};

const useStore = create<State>(set => ({
    payload: [],
    setPayload: (payload) => set({ payload }),
    // setPayload: () => (state) => set({ payload: state }),
}));

export const useFeatureImportanceStore = useStore;