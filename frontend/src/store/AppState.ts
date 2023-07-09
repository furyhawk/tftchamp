import create from 'zustand'
// http://localhost:8000/match/?platform=na1&skip=0&limit=5
const voting = "https://api.github.com/search/users?q=john&per_page=5";
const useStore = create((set) => ({
  voting: voting,
  Votes: {},
  fetch: async (voting: RequestInfo | URL) => {
    const response = await fetch(voting);
    const json = await response.json();
    set({ Votes: json.items })
  },
}))

export default useStore;