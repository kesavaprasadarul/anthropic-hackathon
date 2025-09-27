import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  Home, 
  CheckSquare, 
  Bell, 
  Settings, 
  Menu,
  X,
  Sparkles
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const navItems = [
  { icon: Home, label: 'Home', path: '/' },
  { icon: CheckSquare, label: 'Tasks', path: '/tasks' },
  { icon: Bell, label: 'Notifications', path: '/notifications' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

interface SidebarNavProps {
  className?: string
}

export default function SidebarNav({ className }: SidebarNavProps) {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()
  
  const toggleSidebar = () => setIsOpen(!isOpen)
  
  return (
    <>
      {/* Trigger Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleSidebar}
        className={`fixed top-4 left-4 z-50 jarvis-touch-target bg-space-light/80 backdrop-blur-sm 
          border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/20 hover:border-neon-cyan/50 
          transition-all duration-300 ${className}`}
      >
        <motion.div
          animate={{ rotate: isOpen ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          {isOpen ? <X size={20} /> : <Menu size={20} />}
        </motion.div>
      </Button>
      
      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={toggleSidebar}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />
        )}
      </AnimatePresence>
      
      {/* Sidebar */}
      <AnimatePresence>
        {isOpen && (
          <motion.nav
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 h-full w-72 bg-space-darker/95 backdrop-blur-xl 
              border-r border-neon-cyan/20 z-50 jarvis-card shadow-neon"
          >
            {/* Header */}
            <div className="p-6 border-b border-neon-cyan/20">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="flex items-center gap-3"
              >
                <div className="w-10 h-10 rounded-full bg-gradient-neon flex items-center justify-center">
                  <Sparkles size={20} className="text-space-dark" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-text-primary jarvis-text-glow">Jarvis</h2>
                  <p className="text-sm text-text-secondary">AI Assistant</p>
                </div>
              </motion.div>
            </div>
            
            {/* Navigation Items */}
            <div className="p-4 space-y-2">
              {navItems.map((item, index) => {
                const isActive = location.pathname === item.path
                const Icon = item.icon
                
                return (
                  <motion.div
                    key={item.path}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.1 + index * 0.05 }}
                  >
                    <NavLink
                      to={item.path}
                      onClick={toggleSidebar}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                        isActive 
                          ? 'bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30 jarvis-glow' 
                          : 'text-text-secondary hover:text-text-primary hover:bg-space-light/50'
                      }`}
                    >
                      <Icon 
                        size={20} 
                        className={`transition-transform duration-200 group-hover:scale-110 ${
                          isActive ? 'text-neon-cyan' : ''
                        }`} 
                      />
                      <span className="font-medium">{item.label}</span>
                      {isActive && (
                        <motion.div
                          layoutId="activeIndicator"
                          className="ml-auto w-2 h-2 rounded-full bg-neon-cyan"
                        />
                      )}
                    </NavLink>
                  </motion.div>
                )
              })}
            </div>
            
            {/* Footer */}
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-neon-cyan/20">
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-center"
              >
                <p className="text-xs text-text-tertiary">
                  "Say it once, forget it"
                </p>
              </motion.div>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </>
  )
}