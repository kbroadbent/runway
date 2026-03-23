import { writable } from 'svelte/store';

export const tierFilter = writable<number | null>(null);
export const searchFilter = writable<string>('');
