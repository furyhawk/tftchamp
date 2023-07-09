type Match = {
    id: string;
    match_id: string;
    placement: number;
    augment0: string;
    augment1: string;
    augment2: string;
}

export interface State {
    uri: string;
    Match: [];
    fetch: (uri: string) => Match[];
}

// type State = {
//   voting: string;
//   Votes: object;
//   fetch: (firstName: string) => void;
// };