import { redirect } from '@sveltejs/kit';
export function load() {
	// ...
	redirect(302, '/dashboard'); // needs `throw` in v1
}
