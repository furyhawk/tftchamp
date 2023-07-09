import create from "zustand";

// type State = {
//   voting: string;
//   Votes: object;
//   fetch: (firstName: string) => void;
// };

const voting = "https://api.github.com/search/users?q=john&per_page=5";
const useStore = create((set) => ({
  voting: voting,
  Votes: {},
  fetch: async (voting) => { //: RequestInfo | URL
    const response = await fetch(voting);
    const json = await response.json();
    set({ Votes: json.items })
  },
}))

function Vote() {

  const votes = useStore((state) => state.Votes)

  const fetch = useStore(state => state.fetch)

  return (

    <div>

      <h1>{votes.length} people have cast their votes</h1>

      <button onClick={() => { fetch(voting) }}>Fetch votes</button>

    </div>

  );

}

export default Vote;