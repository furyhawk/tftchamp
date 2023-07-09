import create from 'zustand';

type State = {
    league: string;
    setLeague: (league: string) => void;
};

const useStore = create<State>(set => ({
    league: 'challengers',
    setLeague: (league) => set({ league }),
}));

export const useLeagueStore = useStore;