import create from 'zustand';

type State = {
    region: string;
    setRegion: (region: string) => void;
};

const useStore = create<State>(set => ({
    region: 'na1',
    setRegion: (region) => set({ region }),
}));

export const useRegionStore = useStore;