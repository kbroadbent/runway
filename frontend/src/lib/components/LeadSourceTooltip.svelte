<script lang="ts">
	import { LEAD_SOURCE_LABELS, LEAD_SOURCE_DESCRIPTIONS } from '$lib/types';
	import type { LeadSource } from '$lib/types';

	let showTooltip = $state(false);

	const entries = Object.entries(LEAD_SOURCE_LABELS) as [LeadSource, string][];
</script>

<span class="tooltip-wrapper">
	<button
		class="help-icon"
		onclick={() => (showTooltip = !showTooltip)}
		onmouseenter={() => (showTooltip = true)}
		onmouseleave={() => (showTooltip = false)}
		aria-label="Lead source help"
	>
		?
	</button>
	{#if showTooltip}
		<div class="tooltip-popup">
			{#each entries as [key, label]}
				<div class="tooltip-item">
					<strong>{label}</strong>
					<span>{LEAD_SOURCE_DESCRIPTIONS[key]}</span>
				</div>
			{/each}
		</div>
	{/if}
</span>

<style>
	.tooltip-wrapper {
		position: relative;
		display: inline-flex;
		align-items: center;
	}

	.help-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		height: 16px;
		border-radius: 50%;
		border: 1px solid var(--text-muted, #888);
		background: none;
		color: var(--text-muted, #888);
		font-size: 0.65rem;
		font-weight: 700;
		cursor: pointer;
		padding: 0;
		line-height: 1;
	}

	.help-icon:hover {
		color: var(--text-primary);
		border-color: var(--text-primary);
	}

	.tooltip-popup {
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		margin-top: 0.4rem;
		background: var(--bg-secondary, #1a1a2e);
		border: 1px solid var(--border-color, #333);
		border-radius: var(--radius, 6px);
		padding: 0.6rem 0.75rem;
		z-index: 200;
		width: 260px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}

	.tooltip-item {
		margin-bottom: 0.4rem;
		font-size: 0.8rem;
		line-height: 1.3;
	}

	.tooltip-item:last-child {
		margin-bottom: 0;
	}

	.tooltip-item strong {
		display: block;
		color: var(--text-primary);
		font-size: 0.8rem;
	}

	.tooltip-item span {
		color: var(--text-secondary);
		font-size: 0.75rem;
	}
</style>
