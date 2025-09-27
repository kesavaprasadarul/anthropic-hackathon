import { useRef, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Sphere, Float, Stars } from '@react-three/drei'
import { Mesh, Color } from 'three'
import { motion } from 'framer-motion'

type SphereState = 'idle' | 'listening' | 'thinking' | 'processing'

interface Sphere3DProps {
  state: SphereState
  onTap?: () => void
  onHold?: () => void
  className?: string
}

// Animated sphere component inside the canvas
function AnimatedSphere({ state }: { state: SphereState }) {
  const sphereRef = useRef<Mesh>(null)
  const particlesRef = useRef<any>(null)
  
  // Color mapping for different states
  const stateColors = {
    idle: '#06B6D4',      // neon-cyan
    listening: '#00D9FF',  // neon-teal
    thinking: '#3B82F6',   // neon-blue
    processing: '#D946EF'  // neon-magenta
  }
  
  useFrame((_, delta) => {
    if (sphereRef.current) {
      // Gentle rotation and floating
      sphereRef.current.rotation.y += delta * 0.2
      sphereRef.current.rotation.x += delta * 0.1
      
      // State-specific animations
      console.log('🎭 Sphere animating with state:', state)
      switch (state) {
        case 'listening':
          sphereRef.current.scale.setScalar(1 + Math.sin(Date.now() * 0.005) * 0.1)
          break
        case 'thinking':
        case 'processing':
          sphereRef.current.rotation.y += delta * 0.5
          break
        default:
          sphereRef.current.scale.setScalar(1)
      }
    }
    
    // Animate particles for thinking state
    if (particlesRef.current && (state === 'thinking' || state === 'processing')) {
      particlesRef.current.rotation.y += delta * 0.3
    }
  })
  
  return (
    <>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.8}>
        {/* Main sphere */}
        <Sphere ref={sphereRef} args={[1.5, 64, 64]}>
          <meshPhysicalMaterial
            color={new Color(stateColors[state])}
            transparent
            opacity={0.7}
            roughness={0.1}
            metalness={0.9}
            clearcoat={1}
            clearcoatRoughness={0}
            transmission={0.3}
            thickness={0.5}
          />
        </Sphere>
        
        {/* Outer glow sphere */}
        <Sphere args={[1.8, 32, 32]}>
          <meshBasicMaterial
            color={new Color(stateColors[state])}
            transparent
            opacity={0.1}
          />
        </Sphere>
      </Float>
      
      {/* Thinking particles */}
      {(state === 'thinking' || state === 'processing') && (
        <group ref={particlesRef}>
          <Stars
            radius={3}
            depth={50}
            count={200}
            factor={4}
            saturation={0}
            fade
            speed={0.5}
          />
        </group>
      )}
      
      {/* Ambient lighting */}
      <ambientLight intensity={0.2} />
      <pointLight 
        position={[10, 10, 10]} 
        intensity={0.8}
        color={new Color(stateColors[state])}
      />
    </>
  )
}

export default function Sphere3D({ state, onTap, onHold, className }: Sphere3DProps) {
  const [isPressed, setIsPressed] = useState(false)
  
  const handleTouchStart = () => {
    setIsPressed(true)
    onHold?.()
  }
  
  const handleTouchEnd = () => {
    setIsPressed(false)
    onTap?.()
  }
  
  return (
    <motion.div
      className={`relative ${className}`}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleTouchStart}
      onMouseUp={handleTouchEnd}
      style={{
        filter: isPressed ? 'brightness(1.3)' : 'brightness(1)',
        transition: 'filter 0.2s ease',
      }}
    >
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [0, 0, 6], fov: 45 }}
        style={{ width: '100%', height: '100%' }}
      >
        <AnimatedSphere state={state} />
      </Canvas>
      
      {/* Interaction overlay */}
      <div className="absolute inset-0 rounded-full bg-gradient-sphere opacity-20 pointer-events-none" />
      
      {/* State-based glow effect */}
      <div 
        className={`absolute inset-0 rounded-full transition-all duration-300 pointer-events-none ${
          state === 'idle' ? 'shadow-sphere' :
          state === 'listening' ? 'shadow-[0_0_60px_hsl(var(--neon-teal)/0.8)]' :
          (state === 'thinking' || state === 'processing') ? 'shadow-[0_0_60px_hsl(var(--neon-blue)/0.8)]' :
          'shadow-[0_0_60px_hsl(var(--neon-magenta)/0.8)]'
        }`}
      />
    </motion.div>
  )
}