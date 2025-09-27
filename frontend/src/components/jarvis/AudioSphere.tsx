import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { motion } from 'framer-motion'
import * as THREE from 'three'

interface AudioSphereProps {
  bassLevel: number
  midLevel: number  
  trebleLevel: number
  overallLevel: number
  isActive: boolean
  isSpeaking?: boolean
  onInteraction?: () => void
  className?: string
}

// Audio-reactive sphere component
function ReactiveSphereMesh({ 
  bassLevel, 
  midLevel, 
  trebleLevel, 
  overallLevel,
  isActive,
  isSpeaking 
}: {
  bassLevel: number
  midLevel: number
  trebleLevel: number
  overallLevel: number
  isActive: boolean
  isSpeaking?: boolean
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const materialRef = useRef<THREE.MeshPhongMaterial>(null)
  const geometryRef = useRef<THREE.SphereGeometry>(null)
  const originalPositionsRef = useRef<Float32Array | null>(null)
  const transitionRef = useRef<number>(0) // For smooth transitions
  
  // Create sphere geometry with higher detail for smooth deformation
  const geometry = useMemo(() => {
    const geo = new THREE.SphereGeometry(1, 64, 32)
    return geo
  }, [])

  // Store original vertex positions on first render
  if (!originalPositionsRef.current && geometry.attributes.position) {
    originalPositionsRef.current = geometry.attributes.position.array.slice() as Float32Array
  }

  useFrame((state) => {
    if (!meshRef.current || !materialRef.current || !geometryRef.current) return

    const time = state.clock.elapsedTime
    const mesh = meshRef.current
    const material = materialRef.current
    const geo = geometryRef.current

    // Smooth transition between states (0 = idle, 1 = active)
    const targetTransition = isActive ? 1 : 0
    const transitionSpeed = 0.05 // Adjust for faster/slower transitions
    transitionRef.current += (targetTransition - transitionRef.current) * transitionSpeed
    const transition = transitionRef.current

    // Always apply base rotation and floating animation (both active and inactive)
    mesh.rotation.y = time * 0.2
    mesh.rotation.x = Math.sin(time * 0.15) * 0.1
    mesh.rotation.z = Math.cos(time * 0.1) * 0.05
    
    // Gentle floating motion
    mesh.position.y = Math.sin(time * 0.8) * 0.1

    // Smooth audio-reactive scaling
    const baseScale = 1 + (overallLevel * 0.3 * transition)
    mesh.scale.setScalar(baseScale)

    // Vertex deformation with smooth transition
    if (originalPositionsRef.current && geo.attributes.position) {
      const positions = geo.attributes.position.array as Float32Array
      const originalPositions = originalPositionsRef.current

      for (let i = 0; i < positions.length; i += 3) {
        const x = originalPositions[i]
        const y = originalPositions[i + 1] 
        const z = originalPositions[i + 2]

        // Create vertex normal for displacement direction
        const vertex = new THREE.Vector3(x, y, z)
        const normal = vertex.clone().normalize()

        // Audio-reactive displacement with smooth transition (increased for better visibility)
        const bassNoise = Math.sin(time * 2 + vertex.x * 3) * bassLevel * 0.25 * transition
        const midNoise = Math.sin(time * 4 + vertex.y * 5) * midLevel * 0.15 * transition
        const trebleNoise = Math.sin(time * 8 + vertex.z * 8) * trebleLevel * 0.08 * transition
        
        const displacement = bassNoise + midNoise + trebleNoise

        // Apply displacement along normal
        positions[i] = x + normal.x * displacement
        positions[i + 1] = y + normal.y * displacement
        positions[i + 2] = z + normal.z * displacement
      }

      geo.attributes.position.needsUpdate = true
      geo.computeVertexNormals()
    }

    // Smooth material appearance transitions
    const idleGlow = 0.15 + Math.sin(time * 1.5) * 0.1
    
    // Different colors for user speech vs AI speech
    const idleHue = 0.5 // Cyan
    const userSpeechHue = 0.75 + ((bassLevel * 0.2 + midLevel * 0.15 + trebleLevel * 0.1) % 1) * 0.15 // Purple range
    const aiSpeechHue = 0.08 + ((bassLevel * 0.15 + midLevel * 0.1 + trebleLevel * 0.05) % 1) * 0.1 // Orange/amber range
    
    const activeHue = isSpeaking ? aiSpeechHue : userSpeechHue
    const currentHue = idleHue + (activeHue - idleHue) * transition
    
    // Interpolate saturation
    const idleSaturation = 0.9
    const activeSaturation = 0.85
    const currentSaturation = idleSaturation + (activeSaturation - idleSaturation) * transition
    
    // Interpolate lightness
    const idleLightness = 0.6 + idleGlow
    const activeLightness = 0.7 + overallLevel * 0.3
    const currentLightness = idleLightness + (activeLightness - idleLightness) * transition
    
    material.color.setHSL(currentHue, currentSaturation, currentLightness)
    
    // Interpolate emissive
    const idleEmissive = 0.25 + idleGlow * 0.6
    const activeEmissive = 0.3 + overallLevel * 0.5
    const currentEmissive = idleEmissive + (activeEmissive - idleEmissive) * transition
    
    material.emissive.setHSL(currentHue, currentSaturation * 0.9, currentEmissive)
    
    // Interpolate opacity
    const idleOpacity = 0.85
    const activeOpacity = 0.9 + overallLevel * 0.1
    material.opacity = idleOpacity + (activeOpacity - idleOpacity) * transition
  })

  return (
    <mesh ref={meshRef}>
      <primitive object={geometry} ref={geometryRef} />
      <meshPhongMaterial 
        ref={materialRef}
        transparent
        wireframe={false}
        shininess={100}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

// Particle system for high-frequency details
function AudioParticles({ 
  trebleLevel, 
  isActive,
  isSpeaking 
}: { 
  trebleLevel: number
  isActive: boolean
  isSpeaking?: boolean 
}) {
  const particlesRef = useRef<THREE.Points>(null)
  const transitionRef = useRef<number>(0) // For smooth particle transitions
  
  const { geometry, material } = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    const positions = new Float32Array(100 * 3) // 100 particles
    
    // Distribute particles on sphere surface
    for (let i = 0; i < 100; i++) {
      const phi = Math.acos(-1 + (2 * i) / 100)
      const theta = Math.sqrt(100 * Math.PI) * phi
      
      const x = 1.2 * Math.cos(theta) * Math.sin(phi)
      const y = 1.2 * Math.sin(theta) * Math.sin(phi)  
      const z = 1.2 * Math.cos(phi)
      
      positions[i * 3] = x
      positions[i * 3 + 1] = y
      positions[i * 3 + 2] = z
    }
    
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    
    const mat = new THREE.PointsMaterial({
      color: 0x00ddff, // Brighter cyan for particles
      size: 0.08, // Increased from 0.02 to make particles more visible
      transparent: true,
      opacity: 0.7 // Increased opacity
    })
    
    return { geometry: geo, material: mat }
  }, [])

  useFrame((state) => {
    if (!particlesRef.current) return
    
    const time = state.clock.elapsedTime
    particlesRef.current.rotation.y = time * 0.2
    
    // Smooth transition for particles
    const targetTransition = isActive ? 1 : 0
    transitionRef.current += (targetTransition - transitionRef.current) * 0.05
    const transition = transitionRef.current
    
    // Interpolate particle properties
    const idleSize = 0.06
    const activeSize = 0.08 + trebleLevel * 0.15
    material.size = idleSize + (activeSize - idleSize) * transition
    
    const idleOpacity = 0.5
    const activeOpacity = 0.4 + trebleLevel * 0.6
    material.opacity = idleOpacity + (activeOpacity - idleOpacity) * transition
    
    // Interpolate particle colors
    const idleColor = new THREE.Color(0x00ddff) // Bright cyan
    const userSpeechColor = new THREE.Color().setHSL(0.75 + trebleLevel * 0.1, 0.8, 0.7) // Purple
    const aiSpeechColor = new THREE.Color().setHSL(0.08 + trebleLevel * 0.05, 0.9, 0.65) // Orange/amber
    
    const activeColor = isSpeaking ? aiSpeechColor : userSpeechColor
    material.color.lerpColors(idleColor, activeColor, transition)
  })

  return (
    <points ref={particlesRef} geometry={geometry} material={material} />
  )
}

// Dynamic lighting that responds to audio
function AudioLighting({ 
  bassLevel, 
  overallLevel, 
  isActive,
  isSpeaking 
}: { 
  bassLevel: number
  overallLevel: number
  isActive: boolean
  isSpeaking?: boolean 
}) {
  const pointLightRef = useRef<THREE.PointLight>(null)
  const transitionRef = useRef<number>(0) // For smooth lighting transitions
  
  useFrame(() => {
    if (!pointLightRef.current) return
    
    // Smooth transition for lighting
    const targetTransition = isActive ? 1 : 0
    transitionRef.current += (targetTransition - transitionRef.current) * 0.05
    const transition = transitionRef.current
    
    // Interpolate light intensity
    const idleIntensity = 0.5
    const activeIntensity = 0.7 + bassLevel * 2.0
    pointLightRef.current.intensity = idleIntensity + (activeIntensity - idleIntensity) * transition
    
    // Interpolate light color
    const idleColor = new THREE.Color().setHSL(0.5, 0.6, 0.7) // Cyan
    const userSpeechColor = new THREE.Color().setHSL(0.75 + bassLevel * 0.2, 0.7, 0.8) // Purple
    const aiSpeechColor = new THREE.Color().setHSL(0.08 + bassLevel * 0.15, 0.8, 0.75) // Orange/amber
    
    const activeColor = isSpeaking ? aiSpeechColor : userSpeechColor
    pointLightRef.current.color.lerpColors(idleColor, activeColor, transition)
  })

  return (
    <>
      <ambientLight intensity={0.2} color="#001122" />
      <pointLight 
        ref={pointLightRef}
        position={[0, 0, 0]} 
        distance={5}
        decay={1}
      />
      <pointLight 
        position={[2, 2, 2]} 
        intensity={0.3} 
        color="#0066ff" 
      />
    </>
  )
}

// Main AudioSphere component
export default function AudioSphere({
  bassLevel,
  midLevel,
  trebleLevel, 
  overallLevel,
  isActive,
  isSpeaking,
  onInteraction,
  className
}: AudioSphereProps) {
  return (
    <motion.div
      className={`relative ${className}`}
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      onClick={onInteraction}
      style={{ cursor: onInteraction ? 'pointer' : 'default' }}
    >
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [0, 0, 3], fov: 50 }}
        gl={{ 
          antialias: true, 
          alpha: true,
          powerPreference: "high-performance"
        }}
      >
        <AudioLighting 
          bassLevel={bassLevel}
          overallLevel={overallLevel}
          isActive={isActive}
          isSpeaking={isSpeaking}
        />
        
        <ReactiveSphereMesh
          bassLevel={bassLevel}
          midLevel={midLevel}
          trebleLevel={trebleLevel}
          overallLevel={overallLevel}
          isActive={isActive}
          isSpeaking={isSpeaking}
        />
        
        <AudioParticles 
          trebleLevel={trebleLevel}
          isActive={isActive}
          isSpeaking={isSpeaking}
        />
      </Canvas>
      
      {/* Background glow effect with smooth transition */}
      <div 
        className="absolute inset-0 -z-10 rounded-full blur-xl transition-all duration-500 ease-out"
        style={{
          background: `radial-gradient(circle, ${
            isActive 
              ? isSpeaking
                ? `hsl(${30 + overallLevel * 20}, 85%, ${30 + overallLevel * 25}%)` // Warm orange/amber glow for AI
                : `hsl(${270 + overallLevel * 30}, 80%, ${25 + overallLevel * 25}%)` // Purple glow for user
              : 'hsl(180, 70%, 20%)' // Cyan glow when idle
          } 0%, transparent 70%)`,
          transform: `scale(${1 + overallLevel * 0.5})`,
          opacity: isActive ? 0.7 + overallLevel * 0.3 : 0.5 // Increased idle opacity
        }}
      />
      
      {/* Interaction hint */}
      {!isActive && onInteraction && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-4 h-4 rounded-full bg-neon-cyan opacity-50"
          />
        </div>
      )}
    </motion.div>
  )
}