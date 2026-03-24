export let currentPathname = '/search';

export function setPathname(path: string) {
	currentPathname = path;
}

export const page = {
	url: {
		get pathname() {
			return currentPathname;
		},
	},
};
