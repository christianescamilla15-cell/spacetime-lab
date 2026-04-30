/**
 * KerrScene3D — Three.js scene of a Kerr black hole's relevant surfaces.
 *
 * Renders concentric meshes around the origin:
 *   - inner horizon r_- (purple wireframe)
 *   - outer horizon r_+ (pink solid — the BH surface)
 *   - ergosphere r_E    (cyan wireframe)
 *
 * Plus optional list of `<GeodesicTrail>` lines for multiple integrated
 * trajectories (each with its own colour), an orbit-control camera, and
 * an invisible equatorial pick-plane that fires `onPickInitialState`
 * when the user clicks on it.
 *
 * The scene uses geometric units G=c=1; one Three.js unit == one M.
 *
 * v2.7 changes vs v2.6:
 *   - `trajectories` (array) replaces `trajectory` (single object)
 *   - `trailFractions` (array) replaces `trailFraction` (single)
 *   - new `onPickInitialState({r, theta, phi})` callback for click-pick
 */

import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars } from '@react-three/drei'
import { useMemo } from 'react'

export default function KerrScene3D({
  mass = 1.0,
  spin = 0.5,
  trajectories = [],
  trailFractions = [],
  height = 520,
  onPickInitialState = null,
}) {
  const M = mass
  const a = spin
  const r_plus = M + Math.sqrt(Math.max(M * M - a * a, 0))
  const r_minus = M - Math.sqrt(Math.max(M * M - a * a, 0))
  const r_ergo_eq = 2 * M

  // Auto camera distance: large enough to fit the largest trajectory
  const cameraDistance = useMemo(() => {
    let maxR = 2 * r_ergo_eq
    for (const t of trajectories) {
      if (!t?.response?.trajectory) continue
      for (const s of t.response.trajectory) {
        if (Math.abs(s.x[1]) > maxR) maxR = Math.abs(s.x[1])
      }
    }
    return Math.max(maxR * 1.6, 8)
  }, [trajectories, r_ergo_eq])

  // Equatorial pick-plane radius (out to where the camera is comfortable)
  const pickRadius = cameraDistance * 0.45

  return (
    <Canvas
      camera={{ position: [cameraDistance, cameraDistance * 0.6, cameraDistance], fov: 45 }}
      style={{ height, background: '#05050a', borderRadius: 12 }}
    >
      <ambientLight intensity={0.4} />
      <pointLight position={[20, 20, 20]} intensity={0.8} />
      <Stars radius={120} depth={40} count={1500} factor={3} fade speed={0.3} />

      {/* Outer horizon r_+ */}
      <mesh>
        <sphereGeometry args={[r_plus, 48, 48]} />
        <meshStandardMaterial
          color="#ff6b9d" transparent opacity={0.85}
          roughness={0.3} metalness={0.2}
        />
      </mesh>

      {/* Inner horizon r_- */}
      {r_minus > 0.05 && (
        <mesh>
          <sphereGeometry args={[r_minus, 32, 32]} />
          <meshStandardMaterial
            color="#a78bfa" transparent opacity={0.55} wireframe
          />
        </mesh>
      )}

      {/* Ergosphere */}
      <mesh>
        <sphereGeometry args={[r_ergo_eq, 48, 48]} />
        <meshStandardMaterial
          color="#00dfff" transparent opacity={0.12} wireframe
        />
      </mesh>

      {/* Equatorial reference disk (visual only, not pickable) */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[r_plus * 1.02, pickRadius, 64]} />
        <meshBasicMaterial color="#1a1a2a" side={2} transparent opacity={0.35} />
      </mesh>

      {/* Pick-plane: invisible disk that fires onClick → (r, theta, phi).
          Sits 0.001 above the visible disk to win the raycast tie. */}
      {onPickInitialState && (
        <mesh
          rotation={[Math.PI / 2, 0, 0]}
          position={[0, 0.001, 0]}
          onClick={(event) => {
            event.stopPropagation()
            const p = event.point  // world coords (x, y, z)
            const r = Math.sqrt(p.x * p.x + p.z * p.z)
            // Equatorial click → theta = π/2; phi from xz plane
            const theta = Math.PI / 2
            const phi = Math.atan2(p.z, p.x)
            // Clamp r to the meaningful exterior
            const rClamped = Math.max(r_plus * 1.05, Math.min(r, pickRadius * 0.95))
            onPickInitialState({ r: rClamped, theta, phi })
          }}
        >
          <ringGeometry args={[r_plus * 1.02, pickRadius, 64]} />
          <meshBasicMaterial side={2} transparent opacity={0.0} />
        </mesh>
      )}

      {/* Geodesic trails (multiple) */}
      {trajectories.map((t, i) =>
        t?.response?.trajectory && t.response.trajectory.length > 1 ? (
          <GeodesicTrail
            key={t.id ?? i}
            trajectory={t.response.trajectory}
            color={t.color || '#fbbf24'}
            fraction={trailFractions[i] ?? 1.0}
          />
        ) : null
      )}

      {/* Spin axis indicator (z) */}
      <mesh position={[0, cameraDistance * 0.42, 0]}>
        <coneGeometry args={[0.2, 0.6, 12]} />
        <meshBasicMaterial color="#fff" transparent opacity={0.4} />
      </mesh>

      <OrbitControls
        enablePan
        autoRotate={false}
        minDistance={r_plus + 0.5}
        maxDistance={cameraDistance * 4}
      />
    </Canvas>
  )
}

/**
 * GeodesicTrail — Boyer-Lindquist (t, r, theta, phi) → Cartesian line.
 *
 * Embedding (visual aid, NOT a geometric statement):
 *   x = r sin(theta) cos(phi)
 *   y = r cos(theta)
 *   z = r sin(theta) sin(phi)
 */
function GeodesicTrail({ trajectory, color = '#fbbf24', fraction = 1.0 }) {
  const positions = useMemo(() => {
    const cut = Math.max(2, Math.floor(trajectory.length * fraction))
    const head = trajectory.slice(0, cut)
    const arr = new Float32Array(head.length * 3)
    head.forEach((s, i) => {
      const [, r, theta, phi] = s.x
      arr[i * 3]     = r * Math.sin(theta) * Math.cos(phi)
      arr[i * 3 + 1] = r * Math.cos(theta)
      arr[i * 3 + 2] = r * Math.sin(theta) * Math.sin(phi)
    })
    return arr
  }, [trajectory, fraction])

  const lastPoint = useMemo(() => {
    if (positions.length < 3) return null
    const i = positions.length - 3
    return [positions[i], positions[i + 1], positions[i + 2]]
  }, [positions])

  return (
    <group>
      <line key={positions.length /* force rebuild on length change */}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={positions.length / 3}
            array={positions}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color={color} linewidth={2} />
      </line>
      {lastPoint && (
        <mesh position={lastPoint}>
          <sphereGeometry args={[0.18, 16, 16]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.8} />
        </mesh>
      )}
    </group>
  )
}
