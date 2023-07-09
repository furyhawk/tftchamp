import create from 'zustand';

type State = {
    region: string;
    league: string;
    latest_version: string;
    latest_patch: string;
    
    setRegion: (region: string) => void;
    setLeague: (league: string) => void;
    setVersion: (latest_version: string) => void;
    setPatch: (latest_patch: string) => void;
};

const useStore = create<State>(set => ({
    region: 'na1',
    league: 'challengers',
    latest_version: '',
    latest_patch: '',

    setRegion: (region) => set({ region }),
    setLeague: (league) => set({ league }),
    setVersion: (latest_version) => set({ latest_version }),
    setPatch: (latest_patch) => set({ latest_patch }),
}));

export const useMetadataStore = useStore;