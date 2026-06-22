import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Brain,
  BookOpen,
  PlusCircle,
  Trash2,
  Settings,
  LogOut,
  Info,
  ChevronDown,
  Layers,
  CheckCircle2,
  Circle,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import type { Subject, Unit, Topic, User } from "@/lib/api"

interface SidebarProps {
  subjects: Subject[]
  selectedSubject: Subject | null
  onSelectSubject: (subject: Subject | null) => void
  units: Unit[]
  selectedTopic: Topic | null
  onSelectTopic: (topic: Topic) => void
  onUploadClick: () => void
  onDeleteSubject: (id: number) => void
  user: User | null
  onLogout: () => void
  onSettingsClick: () => void
  onAboutClick: () => void
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({
  subjects,
  selectedSubject,
  onSelectSubject,
  units,
  selectedTopic,
  onSelectTopic,
  onUploadClick,
  onDeleteSubject,
  user,
  onLogout,
  onSettingsClick,
  onAboutClick,
  isOpen,
  onClose,
}: SidebarProps) {
  const [expandedUnits, setExpandedUnits] = useState<number[]>([])

  const toggleUnit = (unitId: number) => {
    setExpandedUnits((prev) =>
      prev.includes(unitId) ? prev.filter((id) => id !== unitId) : [...prev, unitId]
    )
  }

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ x: isOpen ? 0 : "-100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 bg-card border-r shadow-xl flex flex-col",
          "lg:translate-x-0 lg:static"
        )}
      >
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-primary to-blue-600 text-white relative overflow-hidden">
          <motion.div
            className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white opacity-10 rounded-full blur-xl"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 4, repeat: Infinity }}
          />
          <div className="relative z-10">
            <h1 className="text-2xl font-extrabold flex items-center gap-3">
              <Brain className="h-7 w-7" /> Padho Abhi
            </h1>
            <p className="text-xs mt-1 font-medium tracking-wide opacity-90">AI-POWERED LEARNING</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="absolute top-4 right-4 lg:hidden text-white hover:bg-white/20"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* User Profile */}
        {user && (
          <div className="p-4 bg-muted/50 border-b flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold shadow-md">
                {user.username?.charAt(0).toUpperCase()}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold">{user.username}</span>
                <span className="text-xs text-muted-foreground">Free Plan</span>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={onSettingsClick} aria-label="Settings">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Actions */}
        <div className="p-4 border-b">
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button
              variant="gradient"
              className="w-full"
              onClick={onUploadClick}
            >
              <PlusCircle className="h-4 w-4" />
              New Subject
            </Button>
          </motion.div>
        </div>

        {/* Subject Selector */}
        <div className="p-4 border-b">
          <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2 block">
            Current Subject
          </label>
          <Select
            value={selectedSubject?.id.toString() || ""}
            onValueChange={(value) => {
              const subj = subjects.find((s) => s.id === parseInt(value))
              onSelectSubject(subj || null)
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a subject..." />
            </SelectTrigger>
            <SelectContent>
              {subjects.map((s) => (
                <SelectItem key={s.id} value={s.id.toString()}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedSubject && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDeleteSubject(selectedSubject.id)}
              className="w-full mt-3 text-destructive border-destructive/30 hover:bg-destructive/10"
            >
              <Trash2 className="h-3 w-3" /> Delete Subject
            </Button>
          )}
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto p-2">
          <div className="space-y-1">
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={onAboutClick}
            >
              <Info className="h-4 w-4 mr-3" /> About Platform
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start text-destructive hover:bg-destructive/10"
              onClick={onLogout}
            >
              <LogOut className="h-4 w-4 mr-3" /> Logout
            </Button>
          </div>

          <hr className="my-4" />

          {units.length > 0 ? (
            <div className="space-y-4 px-2">
              <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider px-2">
                Learning Path
              </h3>
              {units.map((unit, uIdx) => (
                <motion.div
                  key={unit.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: uIdx * 0.1 }}
                >
                  <button
                    onClick={() => toggleUnit(unit.id)}
                    className="flex items-center gap-2 mb-2 px-2 text-primary font-semibold text-sm w-full hover:bg-accent rounded-lg py-2"
                  >
                    <Layers className="h-4 w-4 opacity-70" />
                    <span className="flex-1 text-left">Unit {unit.unit_number}</span>
                    <motion.div
                      animate={{ rotate: expandedUnits.includes(unit.id) ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown className="h-4 w-4" />
                    </motion.div>
                  </button>
                  <AnimatePresence>
                    {expandedUnits.includes(unit.id) && unit.topics && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-1 ml-2 border-l-2 border-border pl-2 overflow-hidden"
                      >
                        {unit.topics.map((topic) => (
                          <button
                            key={topic.id}
                            onClick={() => {
                              onSelectTopic(topic)
                              if (window.innerWidth < 1024) onClose()
                            }}
                            className={cn(
                              "w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all flex items-start gap-2",
                              selectedTopic?.id === topic.id
                                ? "bg-primary/10 text-primary font-semibold border-l-4 border-primary"
                                : "text-muted-foreground hover:bg-accent hover:text-foreground"
                            )}
                          >
                            {topic.has_notes ? (
                              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500" />
                            ) : (
                              <Circle className="h-4 w-4 mt-0.5" />
                            )}
                            <span className="line-clamp-2 leading-tight">{topic.name}</span>
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          ) : subjects.length === 0 ? (
            <div className="p-8 text-center opacity-50 flex flex-col items-center">
              <BookOpen className="h-12 w-12 text-muted-foreground mb-3" />
              <p className="text-sm font-medium">No subjects yet</p>
              <p className="text-xs mt-1 text-muted-foreground">Create one to start!</p>
            </div>
          ) : (
            <div className="p-8 text-center opacity-50">
              <p className="text-sm">Select a subject to view topics</p>
            </div>
          )}
        </div>
      </motion.div>
    </>
  )
}
