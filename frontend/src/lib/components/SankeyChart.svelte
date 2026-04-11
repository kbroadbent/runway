<script lang="ts">
	import { onMount } from 'svelte';
	import type { FunnelResponse } from '$lib/types';

	interface Props {
		data: FunnelResponse;
	}

	let { data }: Props = $props();

	let svgEl = $state<SVGSVGElement | null>(null);
	let containerEl = $state<HTMLDivElement | null>(null);

	const EXCLUDED_STAGES = new Set(['Interested', 'Applying']);

	const STAGE_ORDER: Record<string, number> = {
		'Applied': 0,
		'Recruiter Screen': 1,
		'Manager Screen': 2,
		'Tech Screen': 3,
		'Onsite': 4,
		'Offer': 5,
		'Rejected': 6,
		'Withdrawn': 6,
		'Archived': 6,
	};

	function getLinkColor(target: string): string {
		switch (target) {
			case 'Rejected': return 'rgba(248, 113, 113, 0.4)';
			case 'Withdrawn': return 'rgba(251, 191, 36, 0.4)';
			case 'Archived': return 'rgba(100, 116, 139, 0.4)';
			case 'Offer': return 'rgba(52, 211, 153, 0.4)';
			default: return 'rgba(148, 163, 184, 0.15)';
		}
	}

	function getLinkHoverColor(target: string): string {
		switch (target) {
			case 'Rejected': return 'rgba(248, 113, 113, 0.7)';
			case 'Withdrawn': return 'rgba(251, 191, 36, 0.7)';
			case 'Archived': return 'rgba(100, 116, 139, 0.7)';
			case 'Offer': return 'rgba(52, 211, 153, 0.7)';
			default: return 'rgba(148, 163, 184, 0.35)';
		}
	}

	function getNodeColor(name: string): string {
		if (name === 'Rejected') return '#f87171';
		if (name === 'Withdrawn') return '#fbbf24';
		if (name === 'Archived') return '#64748b';
		if (name === 'Offer') return '#34d399';
		return '#60a5fa';
	}

	type SankeyNode = { name: string };
	type SankeyLink = { source: number; target: number; value: number };

	function buildGraph(funnelData: FunnelResponse): { nodes: SankeyNode[]; links: SankeyLink[] } | null {
		if (funnelData.transitions.length === 0) return null;

		const stageSet = new Set<string>();
		for (const t of funnelData.transitions) {
			if (!EXCLUDED_STAGES.has(t.from_stage) && !EXCLUDED_STAGES.has(t.to_stage)) {
				stageSet.add(t.from_stage);
				stageSet.add(t.to_stage);
			}
		}

		const stages = [...stageSet].sort((a, b) => (STAGE_ORDER[a] ?? 99) - (STAGE_ORDER[b] ?? 99));
		const nodeIndex = new Map(stages.map((s, i) => [s, i]));
		const nodes = stages.map((name) => ({ name }));

		// Filter out excluded stages and backward transitions (cycles break d3-sankey)
		const links: SankeyLink[] = funnelData.transitions
			.filter((t) => {
				if (EXCLUDED_STAGES.has(t.from_stage) || EXCLUDED_STAGES.has(t.to_stage)) return false;
				const fromOrder = STAGE_ORDER[t.from_stage] ?? 99;
				const toOrder = STAGE_ORDER[t.to_stage] ?? 99;
				return toOrder > fromOrder;
			})
			.map((t) => ({
				source: nodeIndex.get(t.from_stage)!,
				target: nodeIndex.get(t.to_stage)!,
				value: t.count,
			}));

		return { nodes, links };
	}

	async function renderChart(svg: SVGSVGElement, container: HTMLDivElement, funnelData: FunnelResponse) {
		const graph = buildGraph(funnelData);
		if (!graph) return;

		const [{ sankey, sankeyLinkHorizontal }, { select }] = await Promise.all([
			import('d3-sankey'),
			import('d3-selection'),
		]);

		const width = container.clientWidth;
		const height = Math.max(300, Math.min(500, width * 0.45));
		const margin = { top: 10, right: 140, bottom: 10, left: 10 };

		// Clear previous render
		select(svg).selectAll('*').remove();

		select(svg)
			.attr('width', width)
			.attr('height', height)
			.attr('viewBox', `0 0 ${width} ${height}`);

		const sankeyGenerator = sankey<SankeyNode, SankeyLink>()
			.nodeWidth(12)
			.nodePadding(16)
			.nodeSort((a: any, b: any) => {
				const aOrder = STAGE_ORDER[a.name] ?? 99;
				const bOrder = STAGE_ORDER[b.name] ?? 99;
				return aOrder - bOrder;
			})
			.extent([
				[margin.left, margin.top],
				[width - margin.right, height - margin.bottom],
			]);

		const { nodes, links } = sankeyGenerator({
			nodes: graph.nodes.map((d) => ({ ...d })),
			links: graph.links.map((d) => ({ ...d })),
		});

		const svgSel = select(svg);

		// Draw links
		const linkPath = sankeyLinkHorizontal();

		svgSel
			.append('g')
			.attr('fill', 'none')
			.selectAll('path')
			.data(links)
			.join('path')
			.attr('d', linkPath as any)
			.attr('stroke', (d: any) => getLinkColor(d.target.name))
			.attr('stroke-width', (d: any) => Math.max(1, d.width))
			.attr('opacity', 1)
			.on('mouseenter', function (_event: any, d: any) {
				select(this).attr('stroke', getLinkHoverColor(d.target.name));
			})
			.on('mouseleave', function (_event: any, d: any) {
				select(this).attr('stroke', getLinkColor(d.target.name));
			})
			.append('title')
			.text((d: any) => `${d.source.name} → ${d.target.name}: ${d.value}`);

		// Draw nodes
		svgSel
			.append('g')
			.selectAll('rect')
			.data(nodes)
			.join('rect')
			.attr('x', (d: any) => d.x0)
			.attr('y', (d: any) => d.y0)
			.attr('width', (d: any) => d.x1 - d.x0)
			.attr('height', (d: any) => Math.max(1, d.y1 - d.y0))
			.attr('fill', (d: any) => getNodeColor(d.name))
			.attr('rx', 2)
			.append('title')
			.text((d: any) => `${d.name}: ${d.value}`);

		// Draw labels
		svgSel
			.append('g')
			.selectAll('text')
			.data(nodes)
			.join('text')
			.attr('x', (d: any) => (d.x0 < width / 2 ? d.x1 + 8 : d.x0 - 8))
			.attr('y', (d: any) => (d.y0 + d.y1) / 2)
			.attr('dy', '0.35em')
			.attr('text-anchor', (d: any) => (d.x0 < width / 2 ? 'start' : 'end'))
			.attr('fill', '#e2e8f0')
			.attr('font-size', '12px')
			.attr('font-family', 'inherit')
			.text((d: any) => `${d.name}`)
			.append('tspan')
			.attr('fill', '#94a3b8')
			.attr('font-size', '11px')
			.text((d: any) => `  ${d.value}`);
	}

	let mounted = $state(false);

	onMount(() => {
		mounted = true;
	});

	$effect(() => {
		if (mounted && svgEl && containerEl && data) {
			renderChart(svgEl, containerEl, data);
		}
	});
</script>

<div class="sankey-container" bind:this={containerEl}>
	<svg bind:this={svgEl}></svg>
</div>

<style>
	.sankey-container {
		width: 100%;
		min-width: 640px;
		overflow-x: auto;
	}

	svg {
		display: block;
	}
</style>
