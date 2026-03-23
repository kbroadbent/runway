<script lang="ts">
	import type { PipelineComment } from '$lib/types';
	import { pipeline, pipelineComments } from '$lib/api';
	import { onMount } from 'svelte';

	interface Props {
		entryId: number;
	}

	let { entryId }: Props = $props();

	let comments = $state<PipelineComment[]>([]);
	let newContent = $state('');
	let editingId = $state<number | null>(null);
	let editContent = $state('');

	onMount(async () => {
		comments = await pipeline.comments(entryId);
	});

	async function addComment() {
		if (!newContent.trim()) return;
		await pipeline.addComment(entryId, { content: newContent.trim() });
		comments = await pipeline.comments(entryId);
		newContent = '';
	}

	function startEdit(comment: PipelineComment) {
		editingId = comment.id;
		editContent = comment.content;
	}

	function cancelEdit() {
		editingId = null;
		editContent = '';
	}

	async function saveEdit(id: number) {
		await pipelineComments.update(id, { content: editContent.trim() });
		comments = await pipeline.comments(entryId);
		editingId = null;
		editContent = '';
	}

	async function deleteComment(id: number) {
		if (!confirm('Delete this comment?')) return;
		await pipelineComments.delete(id);
		comments = comments.filter((c) => c.id !== id);
	}

	function formatDate(dateStr: string): string {
		const d = new Date(dateStr);
		return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}
</script>

<div class="comments">
	{#if comments.length === 0}
		<p class="empty-hint">No comments yet.</p>
	{/if}

	{#each comments as comment}
		<div class="comment">
			{#if editingId === comment.id}
				<textarea bind:value={editContent} rows={3} style="width:100%" onkeydown={(e) => { if (e.ctrlKey && e.key === 'Enter' && editContent.trim()) saveEdit(comment.id); }}></textarea>
				<div class="comment-actions">
					<button class="btn btn-primary btn-sm" onclick={() => saveEdit(comment.id)} disabled={!editContent.trim()}>Save</button>
					<button class="btn btn-secondary btn-sm" onclick={cancelEdit}>Cancel</button>
				</div>
			{:else}
				<p class="comment-content">{comment.content}</p>
				<div class="comment-footer">
					<span class="comment-date">{formatDate(comment.created_at)}</span>
					{#if comment.updated_at !== comment.created_at}
						<span class="comment-edited">(edited)</span>
					{/if}
					<div class="comment-actions">
						<button class="btn-link" onclick={() => startEdit(comment)}>Edit</button>
						<button class="btn-link danger" onclick={() => deleteComment(comment.id)}>Delete</button>
					</div>
				</div>
			{/if}
		</div>
	{/each}

	<div class="add-comment">
		<textarea bind:value={newContent} rows={2} placeholder="Add a comment..." style="width:100%" onkeydown={(e) => { if (e.ctrlKey && e.key === 'Enter') addComment(); }}></textarea>
		<button class="btn btn-primary btn-sm" onclick={addComment} disabled={!newContent.trim()} style="margin-top:0.4rem">
			Add Comment
		</button>
	</div>
</div>

<style>
	.comments {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.comment {
		padding: 0.6rem 0.75rem;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
	}

	.comment-content {
		font-size: 0.9rem;
		white-space: pre-wrap;
		margin-bottom: 0.35rem;
	}

	.comment-footer {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.comment-date {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.comment-edited {
		font-size: 0.75rem;
		color: var(--text-muted);
		font-style: italic;
	}

	.comment-actions {
		display: flex;
		gap: 0.4rem;
		margin-left: auto;
	}

	.btn-link {
		background: none;
		border: none;
		color: var(--text-secondary);
		font-size: 0.75rem;
		cursor: pointer;
		padding: 0;
		text-decoration: underline;
	}

	.btn-link:hover {
		color: var(--text-primary);
	}

	.btn-link.danger:hover {
		color: var(--accent-red, #ef4444);
	}

	.add-comment {
		margin-top: 0.25rem;
	}

	.empty-hint {
		color: var(--text-muted);
		font-size: 0.9rem;
	}
</style>
