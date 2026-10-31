import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Network,
  Search,
  Filter,
  Maximize2,
  Sparkles,
  Info,
  ChevronRight,
  User,
  Briefcase,
  Cpu,
  CheckCircle,
  HelpCircle,
  RefreshCw,
} from 'lucide-react';
import { echoesApi } from '../services/api';
import { MemoryNode } from '../components/MemoryNode';
import type { GraphData, GraphNodeData, EntityType } from '../types';

const nodeTypes = {
  memoryNode: MemoryNode,
};

export const GraphPage: React.FC = () => {
  const navigate = useNavigate();
  const [graphData, setGraphData] = useState<GraphData>({ workspace_id: '', nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Fetch graph from backend or fallback to demo
  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data = await echoesApi.getGraph();
      setGraphData(data);
    } catch {
      setGraphData({ workspace_id: '', nodes: [], edges: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // Compute Layout Positions for Nodes
  useEffect(() => {
    if (!graphData.nodes || graphData.nodes.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    // Filter nodes if filterType or searchQuery is applied
    const filteredNodes = graphData.nodes.filter((n) => {
      const matchesType = filterType === 'ALL' || n.type === filterType;
      const matchesQuery = n.label.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesQuery;
    });

    const activeNodeIds = new Set(filteredNodes.map((n) => n.id));

    // Multi-tier concentric ring layout to avoid node overlap
    const centerX = 450;
    const centerY = 350;
    const NODES_PER_RING = 8;

    const flowNodes: Node[] = filteredNodes.map((n, index) => {
      const ringIndex = Math.floor(index / NODES_PER_RING);
      const indexInRing = index % NODES_PER_RING;
      const countInThisRing = Math.min(NODES_PER_RING, filteredNodes.length - ringIndex * NODES_PER_RING);
      const ringRadius = 200 + ringIndex * 150;

      const angle = (indexInRing / countInThisRing) * 2 * Math.PI + (ringIndex * 0.3);
      const x = centerX + ringRadius * Math.cos(angle);
      const y = centerY + ringRadius * Math.sin(angle);

      return {
        id: n.id,
        type: 'memoryNode',
        position: { x, y },
        data: {
          label: n.label,
          type: n.type,
          mentions: n.mentions,
          selected: selectedNode?.id === n.id,
        },
      };
    });

    // Edges connecting active nodes
    const flowEdges: Edge[] = graphData.edges
      .filter((e) => activeNodeIds.has(e.from) && activeNodeIds.has(e.to))
      .map((e) => ({
        id: e.id,
        source: e.from,
        target: e.to,
        label: e.label,
        animated: true,
        style: { stroke: '#8B5CF6', strokeWidth: 2, opacity: 0.65 },
        labelStyle: { fill: '#F5F3FF', fontSize: 10, fontWeight: 600 },
        labelBgStyle: { fill: '#151521', fillOpacity: 0.85 },
      }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [graphData, filterType, searchQuery, selectedNode]);

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    const raw = graphData.nodes.find((n) => n.id === node.id);
    if (raw) setSelectedNode(raw);
  };

  const connectedEdges = useMemo(() => {
    if (!selectedNode) return [];
    return graphData.edges.filter(
      (e) => e.from === selectedNode.id || e.to === selectedNode.id
    );
  }, [selectedNode, graphData]);

  return (
    <div className="relative h-[calc(100vh-4rem)] w-full flex flex-col overflow-hidden bg-[#09090F]">
      {/* Top Floating Control Bar */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Left: Search & Filter Controls */}
        <div className="flex items-center gap-2 pointer-events-auto bg-[#101019]/90 backdrop-blur-md p-2 rounded-2xl border border-[#232336] shadow-xl">
          <div className="relative flex items-center">
            <Search className="h-4 w-4 text-[#9292A5] ml-2 absolute" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search entities in graph..."
              className="bg-[#151521] text-xs text-[#F5F3FF] pl-8 pr-3 py-1.5 rounded-xl border border-[#232336] focus:outline-none focus:border-[#8B5CF6] w-48 sm:w-64"
            />
          </div>

          <div className="flex items-center gap-1">
            {['ALL', 'PERSON', 'PROJECT', 'TECHNOLOGY', 'DECISION'].map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase transition-all ${
                  filterType === type
                    ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/30'
                    : 'text-[#9292A5] hover:text-[#F5F3FF] hover:bg-[#1E1E30]'
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          <button
            onClick={loadGraph}
            title="Reload from MongoDB & NetworkX"
            className="p-1.5 rounded-lg text-[#9292A5] hover:text-[#F5F3FF] hover:bg-[#1E1E30]"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Right: Legend */}
        <div className="hidden lg:flex items-center gap-4 bg-[#101019]/90 backdrop-blur-md px-3.5 py-2 rounded-2xl border border-[#232336] text-[11px] pointer-events-auto shadow-xl">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" /> Person
          </div>
          <div className="flex items-center gap-1.5 text-violet-400">
            <span className="h-2 w-2 rounded-full bg-violet-400" /> Project
          </div>
          <div className="flex items-center gap-1.5 text-indigo-400">
            <span className="h-2 w-2 rounded-full bg-indigo-400" /> Tech
          </div>
          <div className="flex items-center gap-1.5 text-amber-400">
            <span className="h-2 w-2 rounded-full bg-amber-400" /> Decision
          </div>
        </div>
      </div>

      {/* Main Graph Canvas */}
      <div className="flex-1 w-full h-full">
        {!loading && nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center p-8">
            <div className="h-20 w-20 rounded-3xl bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 flex items-center justify-center">
              <Network className="h-10 w-10 text-[#8B5CF6]/50" />
            </div>
            <div>
              <p className="text-lg font-bold text-[#F5F3FF]">Knowledge graph is empty</p>
              <p className="text-sm text-[#9292A5] mt-1 max-w-sm">
                Upload documents in Sources and Echoes will automatically extract entities and build your memory graph.
              </p>
            </div>
          </div>
        ) : (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.2}
          maxZoom={2.5}
          attributionPosition="bottom-left"
        >
          <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#232336" />
          <Controls position="bottom-left" showInteractive={false} />
          <MiniMap
            position="bottom-right"
            nodeColor={(n) => {
              if (n.data?.type === 'PERSON') return '#10B981';
              if (n.data?.type === 'PROJECT') return '#8B5CF6';
              if (n.data?.type === 'TECHNOLOGY') return '#6366F1';
              if (n.data?.type === 'DECISION') return '#F59E0B';
              return '#64748B';
            }}
            maskColor="rgba(9, 9, 15, 0.7)"
          />
        </ReactFlow>
        )}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute right-4 top-20 bottom-4 w-80 sm:w-96 rounded-2xl border border-[#232336] bg-[#151521]/95 backdrop-blur-xl p-5 shadow-2xl flex flex-col justify-between z-30 animate-in slide-in-from-right duration-200">
          <div>
            <div className="flex items-start justify-between pb-3 border-b border-[#232336]">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-[#A78BFA]">
                  {selectedNode.type} Entity
                </span>
                <h3 className="text-lg font-bold text-[#F5F3FF] mt-0.5">{selectedNode.label}</h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-[#9292A5] hover:text-[#F5F3FF] p-1 rounded-md"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-4">
              <div className="flex items-center justify-between text-xs rounded-xl bg-[#101019] p-3 border border-[#232336]">
                <span className="text-[#9292A5]">Document Citations</span>
                <span className="font-mono font-bold text-[#F5F3FF]">
                  {selectedNode.mentions} references
                </span>
              </div>

              {/* Connected Relationships */}
              <div>
                <span className="text-xs font-semibold text-[#9292A5] block mb-2">
                  Connected Memory Edges ({connectedEdges.length})
                </span>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {connectedEdges.map((edge) => {
                    const isOutgoing = edge.from === selectedNode.id;
                    const otherNodeId = isOutgoing ? edge.to : edge.from;
                    const otherNode = graphData.nodes.find((n) => n.id === otherNodeId);
                    return (
                      <div
                        key={edge.id}
                        className="rounded-xl border border-[#232336] bg-[#101019] p-2.5 text-xs flex items-center justify-between"
                      >
                        <div className="flex flex-col">
                          <span className="font-semibold text-[#F5F3FF]">
                            {otherNode?.label || otherNodeId}
                          </span>
                          <span className="text-[10px] text-[#A78BFA] font-mono">
                            {edge.label} {isOutgoing ? '→' : '←'}
                          </span>
                        </div>
                        <span className="text-[10px] text-[#64647A] font-mono">
                          {edge.evidence_count} evidence
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Action CTA */}
          <div className="pt-3 border-t border-[#232336]">
            <button
              onClick={() => navigate(`/app/search?q=${encodeURIComponent(selectedNode.label)}`)}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#8B5CF6] py-2.5 text-xs font-bold text-white shadow-lg shadow-[#8B5CF6]/30 hover:bg-[#7C3AED] transition-all"
            >
              <Sparkles className="h-4 w-4" />
              Ask Echoes About This Memory
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
