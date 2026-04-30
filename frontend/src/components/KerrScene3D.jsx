/**
 * KerrScene3D — Three.js scene of a Kerr black hole's relevant surfaces.
 *
 * Renders three concentric meshes around the origin:
 *   - inner horizon r_- (purple, semi-transparent)
 *   - outer horizon r_+ (pink, more opaque, blocks light visually)
 *   - ergosphere r_E(θ) at the equatorial plane (cyan, very transparent)
 *
 * Plus a `<GeodesicTrail>` line for the integrated trajectory and an
 * orbit-control camera so the user can spin around.
 *
 * The scene uses geometric units G=c=1; one Three.js unit == one M.
 */

import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars } from '@react-three/drei'
import { useMemo } from 'react'

export default function KerrScene3D({
  mass = 1.0,
  spin = 0.5,
  trajectory = null,
  trailFraction = 1.0,
  height = 520,
}) {
  const M = mass
  const a = spin
  const r_plus = M + Math.sqrt(Math.max(M * M - a * a, 0))
  const r_minus = M - Math.sqrt(Math.max(M * M - a * a, 0))
  const r_ergo_eq = 2 * M

  // Auto camera distance: large enough to fit the trajectory, otherwise
  // sized by the ergosphere
  const cameraDistance = useMemo(() => {
    if (trajectory && trajectory.length) {
      const maxR = Math.max(
        ...trajectory.map((s) => Math.abs(s.x[1])),
        2 * r_ergo_eq,
      )
      return Math.max(maxR * 1.6, 8)
    }
    return Math.max(r_ergo_eq * 4, 8)
  }, [trajectory, r_ergo_eq])

  return (
    <Canvas
      camera={{ position: [cameraDistance, cameraDistance * 0.6, cameraDistance], fov: 45 }}
      style={{ height, background: '#05050a', borderRadius: 12 }}
    >
      <ambientLight intensity={0.4} />
      <pointLight position={[20, 20, 20]} intensity={0.8} />
      <Stars radius={120} depth={40} count={1500} factor={3} fade speed={0.3} />

      {/* Outer horizon r_+ — pink, mostly opaque (the BH "surface") */}
      <mesh>
        <sphereGeometry args={[r_plus, 48, 48]} />
        <meshStandardMaterial
          color="#ff6b9d" transparent opacity={0.85}
          roughness={0.3} metalness={0.2}
        />
      </mesh>

      {/* Inner horizon r_- (Cauchy) — purple, more transparent */}
      {r_minus > 0.05 && (
        <mesh>
          <sphereGeometry args={[r_minus, 32, 32]} />
          <meshStandardMaterial
            color="#a78bfa" transparent opacity={0.55} wireframe
          />
        </mesh>
      )}

      {/* Ergosphere — at θ=π/2 it sits at 2M; we draw a sphere of radius
          2M as a visual approximation. The true shape is oblate; we
          mark it as wireframe so it reads as "boundary layer". */}
      <mesh>
        <sphereGeometry args={[r_ergo_eq, 48, 48]} />
        <meshStandardMaterial
          color="#00dfff" transparent opacity={0.12} wireframe
        />
      </mesh>

      {/* Equatorial reference disk (annulus from r_+ outward) */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[r_plus * 1.02, cameraDistance * 0.45, 64]} />
        <meshBasicMaterial color="#1a1a2a" side={2} transparent opacity={0.35} />
      </mesh>

      {/* Geodesic trail */}
      {trajectory && trajectory.length > 1 && (
        <GeodesicTrail trajectory={trajectory} fraction={trailFraction} />
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
 * GeodesicTrail — renders a Boyer-Lindquist trajectory as a Three.js line.
 *
 * Converts (t, r, theta, phi) → (x, y, z) for visualisation only:
 *   x = r sin(theta) cos(phi)
 *   y = r cos(theta)
 *   z = r sin(theta) sin(phi)
 *
 * (Note: this is a Newtonian-ish embedding and is NOT the curved-space
 * geodesic in any geometric sense — it's a visual aid, not a metric
 * embedding diagram.)
 */
function GeodesicTrail({ trajectory, fraction = 1.0 }) {
  const points = useMemo(() => {
    const cut = Math.max(2, Math.floor(trajectory.length * fraction))
    const head = trajectory.slice(0, cut)
    return head.map((s) => {
      const [, r, theta, phi] = s.x
      return [
        r * Math.sin(theta) * Math.cos(phi),
        r * Math.cos(theta),
        r * Math.sin(theta) * Math.sin(phi),
      ]
    })
  }, [trajectory, fraction])

  // Build BufferGeometry positions
  const positions = useMemo(() => {
    const arr = new Float32Array(points.length * 3)
    points.forEach((p, i) => {
      arr[i * 3] = p[0]; arr[i * 3 + 1] = p[1]; arr[i * 3 + 2] = p[2]
    })
    return arr
  }, [points])

  const lastPoint = points[points.length - 1]

  return (
    <group>
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={points.length}
            array={positions}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#fbbf24" linewidth={2} />
      </line>
      {/* "Current position" marker at the trail head */}
      {lastPoint && (
        <mesh position={lastPoint}>
          <sphereGeometry args={[0.18, 16, 16]} />
          <meshStandardMaterial color="#fbbf24" emissive="#fbbf24" emissiveIntensity={0.8} />
        </mesh>
      )}
    </group>
  )
}
