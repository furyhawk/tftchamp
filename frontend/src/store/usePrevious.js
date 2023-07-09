import { useEffect, useRef } from 'react';

export const usePrevious = (value) => {
    const ref = useRef(0);
    useEffect(() => {
        ref.current = value;
    });
    return ref.current;
}