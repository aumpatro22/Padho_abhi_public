import { motion } from "framer-motion"
import {
  BarChart3,
  BookOpen,
  Copy,
  HelpCircle,
  Bot,
  Menu,
  Sparkles,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface MobileBottomNavProps {
  activeTab: string
  onTabChange: (tab: string) => void
  onMenuClick: () => void
  hasSelectedTopic: boolean
}

const tabs = [
  { id: "dashboard", icon: BarChart3, label: "Home" },
  { id: "notes", icon: BookOpen, label: "Notes" },
  { id: "flashcards", icon: Copy, label: "Cards" },
  { id: "mcqs", icon: HelpCircle, label: "Quiz" },
  { id: "chat", icon: Bot, label: "Ask AI" },
]

export function MobileBottomNav({
  activeTab,
  onTabChange,
  onMenuClick,
  hasSelectedTopic,
}: MobileBottomNavProps) {
  return (
    <motion.div
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className="mobile-bottom-bar md:hidden glass border-t"
    >
      <div className="flex items-center justify-around px-2 py-1">
        {/* Menu Button */}
        <button
          onClick={onMenuClick}
          className="flex flex-col items-center justify-center p-2 min-w-[56px] rounded-xl transition-all active:scale-90"
          aria-label="Open menu"
        >
          <motion.div
            whileTap={{ scale: 0.85 }}
            className="p-2 rounded-xl bg-muted/50"
          >
            <Menu className="h-5 w-5 text-muted-foreground" />
          </motion.div>
          <span className="text-[10px] mt-1 text-muted-foreground font-medium">Menu</span>
        </button>

        {/* Tab Buttons */}
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id
          const isDisabled = tab.id !== "dashboard" && !hasSelectedTopic

          return (
            <button
              key={tab.id}
              onClick={() => !isDisabled && onTabChange(tab.id)}
              disabled={isDisabled}
              className={cn(
                "flex flex-col items-center justify-center p-2 min-w-[56px] rounded-xl transition-all",
                isDisabled && "opacity-40 pointer-events-none"
              )}
            >
              <motion.div
                whileTap={{ scale: 0.85 }}
                className={cn(
                  "p-2 rounded-xl transition-all duration-200",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30"
                    : "bg-transparent text-muted-foreground"
                )}
              >
                <tab.icon className="h-5 w-5" />
                {isActive && (
                  <motion.div
                    layoutId="activeTabIndicator"
                    className="absolute inset-0 rounded-xl bg-primary -z-10"
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
              </motion.div>
              <span
                className={cn(
                  "text-[10px] mt-1 font-medium transition-colors",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              >
                {tab.label}
              </span>
              {isActive && (
                <motion.div
                  layoutId="activeDot"
                  className="w-1 h-1 rounded-full bg-primary mt-0.5"
                />
              )}
            </button>
          )
        })}
      </div>
    </motion.div>
  )
}

// Floating Action Button for quick actions
export function FloatingActionButton({
  onClick,
  icon: Icon = Sparkles,
  label = "New",
}: {
  onClick: () => void
  icon?: React.ElementType
  label?: string
}) {
  return (
    <motion.button
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="fab md:hidden flex items-center gap-2 bg-gradient-to-r from-primary to-purple-600 text-white px-5 py-3.5 rounded-full font-semibold"
    >
      <Icon className="h-5 w-5" />
      <span>{label}</span>
    </motion.button>
  )
}
