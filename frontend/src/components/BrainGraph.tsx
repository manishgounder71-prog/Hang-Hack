'use client'

import { useEffect, useRef, useState, useMemo, useCallback } from 'react'
import { Canvas, useFrame, ThreeEvent } from '@react-three/fiber'
import { OrbitControls, Html, Line } from '@react-three/drei'
import * as THREE from 'three'
import { Brain, AlertCircle, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'

// ─── Types ────────────────────────────────────────────────────────
interface GraphNode {
  id: string
  label: string
  type: string
  importance: number
  properties?: Record<string, any>
  content_type?: string
  created_at?: string
}

interface GraphEdge {
  source: string
  target: string
  label: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  count: number
}

// ─── Color map by node type ───────────────────────────────────────
const NODE_COLORS: Record<string, string> = {
  memory: '#2563eb',
  entity: '#7c3aed',
  project: '#0d9488',
  skill: '#d97706',
  concept: '#ec4899',
  technology: '#10b981',
  achievement: '#f59e0b',
  learning: '#6366f1',
  research: '#06b6d4',
  milestone: '#f43f5e',
  file: '#8b5cf6',
  reflection: '#a855f7',
  prediction: '#14b8a6',
  default: '#6b7280',
}

function getNodeColor(type: string): string {
  return NODE_COLORS[type?.toLowerCase()] || NODE_COLORS.default
}

// ─── 3D Force-Directed Layout ─────────────────────────────────────
function computeForceLayout(nodes: GraphNode[], edges: GraphEdge[]): Float32Array {
  const n = nodes.length
  const positions = new Float32Array(n * 3)
  const velocities = new Float32Array(n * 3)

  // Initialize positions on a sphere
  for (let i = 0; i < n; i++) {
    const theta = (i / n) * Math.PI * 2
    const phi = Math.acos(2 * (i / n) - 1)
    const r = 4 + (Math.random() - 0.5) * 2
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
    positions[i * 3 + 2] = r * Math.cos(phi)
  }

  // Build adjacency map
  const adj: Map<string, Set<string>> = new Map()
  nodes.forEach(n => adj.set(n.id, new Set()))
  edges.forEach(e => {
    adj.get(e.source)?.add(e.target)
    adj.get(e.target)?.add(e.source)
  })

  // Run simulation (50 iterations to balance quality vs performance)
  const iterations = 50
  const repulsion = 8
  const attraction = 0.02
  const damping = 0.85

  for (let iter = 0; iter < iterations; iter++) {
    const nodeMap = new Map(nodes.map((n, i) => [n.id, i]))

    // Repulsion between all nodes
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = positions[j * 3] - positions[i * 3]
        const dy = positions[j * 3 + 1] - positions[i * 3 + 1]
        const dz = positions[j * 3 + 2] - positions[i * 3 + 2]
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
        if (dist < 0.01) continue
        const force = repulsion / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        const fz = (dz / dist) * force
        velocities[i * 3] -= fx
        velocities[i * 3 + 1] -= fy
        velocities[i * 3 + 2] -= fz
        velocities[j * 3] += fx
        velocities[j * 3 + 1] += fy
        velocities[j * 3 + 2] += fz
      }
    }

    // Attraction along edges
    edges.forEach(e => {
      const si = nodeMap.get(e.source)
      const ti = nodeMap.get(e.target)
      if (si === undefined || ti === undefined) return
      const dx = positions[ti * 3] - positions[si * 3]
      const dy = positions[ti * 3 + 1] - positions[si * 3 + 1]
      const dz = positions[ti * 3 + 2] - positions[si * 3 + 2]
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
      const force = dist * attraction
      const fx = (dx / (dist || 1)) * force
      const fy = (dy / (dist || 1)) * force
      const fz = (dz / (dist || 1)) * force
      velocities[si * 3] += fx
      velocities[si * 3 + 1] += fy
      velocities[si * 3 + 2] += fz
      velocities[ti * 3] -= fx
      velocities[ti * 3 + 1] -= fy
      velocities[ti * 3 + 2] -= fz
    })

    // Apply velocities with damping
    for (let i = 0; i < n * 3; i++) {
      velocities[i] *= damping
      positions[i] += velocities[i]
    }

    // Center gravity
    let sumX = 0, sumY = 0, sumZ = 0
    for (let i = 0; i < n; i++) {
      sumX += positions[i * 3]
      sumY += positions[i * 3 + 1]
      sumZ += positions[i * 3 + 2]
    }
    const cx = sumX / n
    const cy = sumY / n
    const cz = sumZ / n
    for (let i = 0; i < n; i++) {
      positions[i * 3] += (0 - cx) * 0.01
      positions[i * 3 + 1] += (0 - cy) * 0.01
      positions[i * 3 + 2] += (0 - cz) * 0.01
    }
  }

  return positions
}

// ─── Edge Line Component ──────────────────────────────────────────
function EdgeLine({ start, end, opacity }: {
  start: [number, number, number]
  end: [number, number, number]
  opacity: number
}) {
  const points = useMemo(() => [new THREE.Vector3(...start), new THREE.Vector3(...end)], [start, end])

  return (
    <Line
      points={points}
      color="#2563eb"
      transparent
      opacity={opacity * 0.4}
      lineWidth={1}
      depthWrite={false}
    />
  )
}

// ─── Particle Flow Component ──────────────────────────────────────
function ParticleFlow({ start, end, speed }: {
  start: [number, number, number]
  end: [number, number, number]
  speed: number
}) {
  const ref = useRef<THREE.Mesh>(null!)
  const [phase] = useState(() => Math.random() * 100)

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = ((clock.elapsedTime * speed * 0.3 + phase) % 1)
    ref.current.position.lerpVectors(
      new THREE.Vector3(...start),
      new THREE.Vector3(...end),
      t
    )
  })

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.04, 6, 6]} />
      <meshBasicMaterial color="#7c3aed" transparent opacity={0.5} depthWrite={false} />
    </mesh>
  )
}

// ─── Node Sphere Component ────────────────────────────────────────
function NodeSphere({
  node,
  position,
  isHovered,
  isSelected,
  onHover,
  onClick,
}: {
  node: GraphNode
  position: [number, number, number]
  isHovered: boolean
  isSelected: boolean
  onHover: (id: string | null) => void
  onClick: (id: string) => void
}) {
  const meshRef = useRef<THREE.Mesh>(null!)
  const glowRef = useRef<THREE.Mesh>(null!)

  const size = 0.15 + (node.importance || 0.5) * 0.35
  const color = getNodeColor(node.type)

  // Hover animation
  useFrame(() => {
    if (!meshRef.current) return
    const current = meshRef.current.scale.x
    const target = isHovered ? 1.4 : 1
    const next = current + (target - current) * 0.1
    meshRef.current.scale.setScalar(next)

    if (glowRef.current) {
      const glowTarget = isHovered ? 1.8 : 1
      const glowNext = glowRef.current.scale.x + (glowTarget - glowRef.current.scale.x) * 0.08
      glowRef.current.scale.setScalar(glowNext)
      const mat = glowRef.current.material as THREE.MeshBasicMaterial
      mat.opacity = isHovered ? 0.4 : 0.15
    }
  })

  const handlePointerOver = useCallback((e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation()
    onHover(node.id)
    document.body.style.cursor = 'pointer'
  }, [node.id, onHover])

  const handlePointerOut = useCallback(() => {
    onHover(null)
    document.body.style.cursor = 'default'
  }, [onHover])

  const handleClick = useCallback((e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation()
    onClick(node.id)
  }, [node.id, onClick])

  return (
    <group position={position}>
      {/* Glow */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[size * 2, 16, 16]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.15}
          depthWrite={false}
        />
      </mesh>

      {/* Core sphere */}
      <mesh
        ref={meshRef}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        onClick={handleClick}
      >
        <sphereGeometry args={[size, 16, 16]} />
        <meshStandardMaterial
          color={color}
          roughness={0.3}
          metalness={0.1}
          emissive={color}
          emissiveIntensity={isHovered ? 0.4 : 0.1}
        />
      </mesh>

      {/* Ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[size * 1.1, size * 1.3, 32]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={isHovered ? 0.3 : 0.1}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>

      {/* Label */}
      {(isHovered || isSelected) && (
        <Html
          position={[0, -size - 0.3, 0]}
          center
          style={{
            pointerEvents: 'none',
          }}
        >
          <span style={{
            fontSize: '10px',
            color: '#e5e7eb',
            background: 'rgba(0,0,0,0.6)',
            padding: '2px 6px',
            borderRadius: '4px',
            whiteSpace: 'nowrap',
            fontFamily: 'Inter, sans-serif',
            maxWidth: '120px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: 'inline-block',
            backdropFilter: 'blur(4px)',
            border: `1px solid ${color}40`,
          }}>
            {node.label}
          </span>
        </Html>
      )}
    </group>
  )
}

// ─── Info Panel for Selected Node ─────────────────────────────────
function InfoPanel({ node, onClose }: { node: GraphNode; onClose: () => void }) {
  return (
    <div className="absolute top-4 right-4 glass-strong rounded-xl p-4 max-w-[220px] z-10">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: getNodeColor(node.type) }}
          />
          <span className="text-xs font-medium">{node.label}</span>
        </div>
        <button
          onClick={onClose}
          className="w-5 h-5 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors text-gray-500"
        >
          ×
        </button>
      </div>
      <div className="space-y-1 text-[10px] text-gray-400">
        <p>Type: <span className="text-gray-300">{node.type}</span></p>
        <p>Importance: <span className="text-gray-300">{Math.round((node.importance || 0.5) * 100)}%</span></p>
        {node.content_type && <p>Content: <span className="text-gray-300">{node.content_type}</span></p>}
        {node.created_at && <p>Created: <span className="text-gray-300">{new Date(node.created_at).toLocaleDateString()}</span></p>}
      </div>
    </div>
  )
}

// ─── 3D Scene (inner component) ───────────────────────────────────
function GraphScene({
  nodes,
  edges,
  positions,
  hoveredNode,
  selectedNode,
  onHover,
  onClick,
}: {
  nodes: GraphNode[]
  edges: GraphEdge[]
  positions: Float32Array
  hoveredNode: string | null
  selectedNode: string | null
  onHover: (id: string | null) => void
  onClick: (id: string) => void
}) {
  // Auto-rotation
  const groupRef = useRef<THREE.Group>(null!)
  useFrame((_, delta) => {
    if (groupRef.current && !hoveredNode) {
      groupRef.current.rotation.y += delta * 0.08
    }
  })

  return (
    <group ref={groupRef}>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.3} color="#7c3aed" />

      {/* Edges */}
      {edges.map((edge, i) => {
        const si = nodes.findIndex(n => n.id === edge.source)
        const ti = nodes.findIndex(n => n.id === edge.target)
        if (si === -1 || ti === -1) return null
        const start: [number, number, number] = [
          positions[si * 3], positions[si * 3 + 1], positions[si * 3 + 2]
        ]
        const end: [number, number, number] = [
          positions[ti * 3], positions[ti * 3 + 1], positions[ti * 3 + 2]
        ]
        const isConnected =
          hoveredNode && (edge.source === hoveredNode || edge.target === hoveredNode)
        const showParticles = edges.length <= 15
        return (
          <group key={`edge-${i}`}>
            <EdgeLine start={start} end={end} opacity={isConnected ? 0.7 : 0.25} />
            {showParticles && (
              <ParticleFlow start={start} end={end} speed={0.5 + (i % 3) * 0.2} />
            )}
          </group>
        )
      })}

      {/* Nodes */}
      {nodes.map((node, i) => (
        <NodeSphere
          key={node.id}
          node={node}
          position={[positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]]}
          isHovered={hoveredNode === node.id}
          isSelected={selectedNode === node.id}
          onHover={onHover}
          onClick={onClick}
        />
      ))}

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        rotateSpeed={0.5}
        zoomSpeed={1}
        minDistance={2}
        maxDistance={20}
        autoRotate={false}
      />
    </group>
  )
}

// ─── Main Exported Component ──────────────────────────────────────
export default function BrainGraph() {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const positions = useMemo(() => {
    if (!graphData) return new Float32Array()
    return computeForceLayout(graphData.nodes, graphData.edges)
  }, [graphData])

  const fetchGraph = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.knowledge.graph()
      if (!data.nodes || data.nodes.length === 0) {
        // Generate sample data if empty
        const sampleNodes: GraphNode[] = [
          { id: '1', label: 'Project Alpha', type: 'project', importance: 0.92 },
          { id: '2', label: 'React', type: 'skill', importance: 0.85 },
          { id: '3', label: 'TypeScript', type: 'skill', importance: 0.78 },
          { id: '4', label: 'AI Memory', type: 'concept', importance: 0.95 },
          { id: '5', label: 'Cognee', type: 'technology', importance: 1.0 },
          { id: '6', label: 'Docker', type: 'skill', importance: 0.65 },
          { id: '7', label: 'Hackathon Win', type: 'achievement', importance: 0.88 },
          { id: '8', label: 'Python', type: 'skill', importance: 0.82 },
          { id: '9', label: 'FastAPI', type: 'technology', importance: 0.75 },
          { id: '10', label: 'PostgreSQL', type: 'technology', importance: 0.7 },
        ]
        const sampleEdges: GraphEdge[] = [
          { source: '1', target: '2', label: 'uses' },
          { source: '1', target: '3', label: 'uses' },
          { source: '1', target: '9', label: 'built with' },
          { source: '4', target: '5', label: 'powered by' },
          { source: '1', target: '6', label: 'deployed with' },
          { source: '1', target: '7', label: 'resulted in' },
          { source: '4', target: '8', label: 'implemented in' },
          { source: '9', target: '10', label: 'connects to' },
          { source: '5', target: '4', label: 'enables' },
          { source: '2', target: '3', label: 'works with' },
        ]
        setGraphData({ nodes: sampleNodes, edges: sampleEdges, count: sampleNodes.length })
      } else {
        setGraphData(data)
      }
    } catch (err) {
      setError('Failed to load knowledge graph')
      setGraphData({
        nodes: [
          { id: '1', label: 'Genesis AI', type: 'concept', importance: 1.0 },
          { id: '2', label: 'Cognee', type: 'technology', importance: 0.95 },
          { id: '3', label: 'Knowledge Graph', type: 'concept', importance: 0.8 },
        ],
        edges: [
          { source: '1', target: '2', label: 'uses' },
          { source: '1', target: '3', label: 'creates' },
        ],
        count: 3,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGraph()
  }, [fetchGraph])

  const handleNodeClick = useCallback((id: string) => {
    setSelectedNode(prev => prev === id ? null : id)
  }, [])

  const selectedNodeData = useMemo(() => {
    if (!selectedNode || !graphData) return null
    return graphData.nodes.find(n => n.id === selectedNode) || null
  }, [selectedNode, graphData])

  const handleRefresh = useCallback(() => {
    setSelectedNode(null)
    fetchGraph()
  }, [fetchGraph])

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center w-full" style={{ minHeight: '250px' }}>
        <div className="text-center">
          <div className="w-10 h-10 rounded-2xl neural-gradient flex items-center justify-center mx-auto mb-3 animate-breathe">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <p className="text-gray-500 text-xs animate-pulse">Connecting neural pathways...</p>
        </div>
      </div>
    )
  }

  // Empty state
  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center w-full" style={{ minHeight: '250px' }}>
        <div className="text-center">
          <Brain className="w-10 h-10 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 text-xs mb-3">No knowledge graph data yet</p>
          <button
            onClick={handleRefresh}
            className="px-3 py-1.5 rounded-lg text-[10px] bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:opacity-90 transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full" style={{ minHeight: '250px', height: '100%' }}>
      {error && (
        <div className="absolute top-2 left-2 right-2 z-10 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px]">
          <AlertCircle className="w-3 h-3 flex-shrink-0" />
          <span className="flex-1">{error} — showing sample data</span>
          <button onClick={handleRefresh} className="hover:text-white transition-colors">
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
      )}

      {selectedNodeData && (
        <InfoPanel node={selectedNodeData} onClose={() => setSelectedNode(null)} />
      )}

      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <GraphScene
          nodes={graphData.nodes}
          edges={graphData.edges}
          positions={positions}
          hoveredNode={hoveredNode}
          selectedNode={selectedNode}
          onHover={setHoveredNode}
          onClick={handleNodeClick}
        />
      </Canvas>

      <div className="absolute bottom-2 left-2 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        <span className="text-[10px] text-gray-600">
          {graphData.nodes.length} nodes · {graphData.edges.length} connections
        </span>
      </div>

      <div className="absolute bottom-2 right-2 flex gap-1.5">
        {['memory', 'entity', 'skill', 'project'].map((type) => (
          <span
            key={type}
            className="text-[8px] px-1.5 py-0.5 rounded-full flex items-center gap-1 bg-white/5 border border-white/10 text-gray-500"
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: getNodeColor(type) }}
            />
            {type}
          </span>
        ))}
      </div>
    </div>
  )
}
