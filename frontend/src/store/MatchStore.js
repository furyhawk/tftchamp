import create from 'zustand'

import axios from '../services/axios'
// import { State } from "../model/Match";

// interface MatchState {
//     todos: State[];
//     addTodo: (description: string) => void;
//     removeTodo: (id: string) => void;
//     toggleCompletedState: (id: string) => void;
// }

const uri = `/match?platform=na1&skip=0&limit=5`;

const useStore = create((set, get) => ({
    uri: uri,
    count: 0,
    Matches: [],
    fetch: async (uri) => { //: RequestInfo | URL
        const response = await axios.get(uri);
        let { results } = response.data;
        let new_array = [...get().Matches, ...results];
        // Unique list
        let res = new_array.splice(1).reduce((acc, elem) => acc.every(({ _id }) => _id !== elem._id) ? [...acc, elem] : acc, [new_array[0]]);
        set({ count: response.data.count });
        set({ Matches: res });
    },
}));

export default useStore;