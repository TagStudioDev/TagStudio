<script>
import "../app.pcss";
import { ParaglideJS } from '@inlang/paraglide-sveltekit'
	import { i18n } from '$lib/i18n'
</script>

<ParaglideJS {i18n}>
    <slot />
</ParaglideJS>