<script lang="ts">
	import { invoke } from '@tauri-apps/api/tauri';

	let name = '';
	let greetingMessage = '';

	async function greet() {
		greetingMessage = await invoke('greet', { name });
	}
</script>

<div class="card flex flex-col gap-4 p-4">
	<label class="label">
		<span>Enter your name</span>
		<input id="gree-input" placeholder="Enter a name..." bind:value={name} class="input" />
	</label>
	<button class="variant-filled btn" on:click={greet}>Greet</button>
	<p class="card-footer">{greetingMessage}</p>
</div>
