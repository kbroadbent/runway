<script lang="ts">
	import type { ClosedPostingAlert } from '$lib/types';
	import { postings as postingsApi } from '$lib/api';

	interface Props {
		items: ClosedPostingAlert[];
	}

	let { items }: Props = $props();
	let localItems = $state<ClosedPostingAlert[]>([]);

	$effect(() => {
		localItems = [...items];
	});

	async function dismiss(id: number) {
		await postingsApi.dismissClosed(id);
		localItems = localItems.filter((item) => item.id !== id);
	}
</script>

{#if localItems.length > 0}
	<div class="closed-postings">
		<h2>Possibly Closed</h2>
		<div class="items-list">
			{#each localItems as item}
				<div class="closed-item">
					<div class="item-left">
						<span class="item-type-badge">Closed</span>
						<div class="item-details">
							{#if item.url}
								<a href={item.url} target="_blank" rel="noopener noreferrer" class="item-title">
									{item.title}
								</a>
							{:else}
								<span class="item-title">{item.title}</span>
							{/if}
							{#if item.company_name}
								<span class="item-company">{item.company_name}</span>
							{/if}
						</div>
					</div>
					<button class="dismiss-btn" onclick={() => dismiss(item.id)}>Dismiss</button>
				</div>
			{/each}
		</div>
	</div>
{/if}

<style>
	.closed-postings {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		padding: 1.25rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 1rem;
	}

	.items-list {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.closed-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.625rem 0.75rem;
		background: var(--bg-tertiary);
		border-radius: var(--radius);
		border-left: 3px solid var(--accent-red);
	}

	.item-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		min-width: 0;
	}

	.item-type-badge {
		font-size: 0.625rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.125rem 0.375rem;
		border-radius: 3px;
		background: var(--bg-primary);
		color: var(--accent-red);
		white-space: nowrap;
	}

	.item-details {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.item-title {
		font-size: 0.875rem;
		color: var(--text-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		text-decoration: none;
	}

	.item-title:hover {
		text-decoration: underline;
	}

	.item-company {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.dismiss-btn {
		padding: 0.25rem 0.625rem;
		font-size: 0.75rem;
		background: none;
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		color: var(--text-secondary);
		cursor: pointer;
		white-space: nowrap;
		transition: background 0.15s, color 0.15s;
	}

	.dismiss-btn:hover {
		background: var(--bg-primary);
		color: var(--text-primary);
	}
</style>
