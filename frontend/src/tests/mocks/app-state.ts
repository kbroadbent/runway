export let currentPathname = '/search';
let currentSearchParams = new URLSearchParams();

export function setPathname(path: string) {
	currentPathname = path;
}

export function setSearchParams(params: Record<string, string>) {
	currentSearchParams = new URLSearchParams(params);
}

export function resetSearchParams() {
	currentSearchParams = new URLSearchParams();
}

export const page = {
	url: {
		get pathname() {
			return currentPathname;
		},
		get searchParams() {
			return currentSearchParams;
		},
	},
};
