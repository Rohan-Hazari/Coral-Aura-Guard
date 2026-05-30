import { useMemo } from 'react';
import { ReactFlow, Background, Controls, type Edge, type Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface GraphProps {
  data: any[];
  rootLabel: string;
}

export default function DependencyGraph({ data, rootLabel }: GraphProps) {
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [
      {
        id: 'root',
        data: { label: rootLabel },
        position: { x: 250, y: 0 },
        style: { background: '#3b82f6', color: 'white', fontWeight: 'bold', borderRadius: '8px', border: 'none', padding: '10px' },
      },
    ];
    const edges: Edge[] = [];

    // Map rows to nodes
    // Each row is {"downstream_repo": "...", "active_pr": 123, "developer": "..."}
    data.forEach((row, i) => {
      const nodeId = `node-${i}`;
      nodes.push({
        id: nodeId,
        data: { 
          label: (
            <div className="text-[10px]">
              <div className="font-bold">{row.downstream_repo}</div>
              <div className="opacity-60 text-[8px]">PR #{row.active_pr} • @{row.developer}</div>
            </div>
          )
        },
        position: { x: i * 200, y: 150 },
        style: { background: '#1f2937', color: 'white', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', width: 150 },
      });

      edges.push({
        id: `e-root-${nodeId}`,
        source: 'root',
        target: nodeId,
        animated: true,
        style: { stroke: '#3b82f6' },
      });
    });

    return { nodes, edges };
  }, [data, rootLabel]);

  return (
    <div style={{ width: '100%', height: '400px' }} className="bg-black/20 rounded-xl border border-white/5 overflow-hidden mt-8">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        colorMode="dark"
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
