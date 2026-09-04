import { useState, useEffect, createContext, useContext } from "react"
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useParams,
  useLocation,
} from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  Menu,
  Sun,
  Moon,
  BookOpen,
  Network,
  Copy,
  HelpCircle,
  Bot,
  CheckCircle2,
  AlertTriangle,
  Plus,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Loading } from "@/components/Loading"
import { AuthPage } from "@/components/AuthPage"
import { Sidebar } from "@/components/Sidebar"
import { SyllabusUploadModal } from "@/components/SyllabusUploadModal"
import { WelcomeScreen } from "@/components/WelcomeScreen"
import { NotesTab } from "@/components/tabs/NotesTab"
import { MindmapTab } from "@/components/tabs/MindmapTab"
import { FlashcardsTab } from "@/components/tabs/FlashcardsTab"
import { MCQTab } from "@/components/tabs/MCQTab"
import { ChatTab } from "@/components/tabs/ChatTab"
import { Dashboard } from "@/components/tabs/Dashboard"
import { SettingsTab } from "@/components/tabs/SettingsTab"
import { AboutTab } from "@/components/tabs/AboutTab"
import { MobileBottomNav, FloatingActionButton } from "@/components/MobileBottomNav"
import { ToastProvider, useToast } from "@/components/Toast"
import { api } from "@/lib/api"
import type { User, Subject, Unit, Topic, Note, Mindmap, Flashcard, MCQ, UserProfile } from "@/lib/api"
import { cn } from "@/lib/utils"

// App context for sharing state
interface AppContextType {
  user: User | null
  setUser: (user: User | null) => void
  subjects: Subject[]
  loadSubjects: () => Promise<void>
  selectedSubject: Subject | null
  setSelectedSubject: (subject: Subject | null) => void
  units: Unit[]
  setUnits: (units: Unit[]) => void
  userProfile: UserProfile | null
  theme: "light" | "dark"
  toggleTheme: () => void
  showUploadModal: boolean
  setShowUploadModal: (show: boolean) => void
  isSidebarOpen: boolean
  setIsSidebarOpen: (open: boolean) => void
}

const AppContext = createContext<AppContextType | null>(null)

export function useAppContext() {
  const context = useContext(AppContext)
  if (!context) throw new Error("useAppContext must be used within AppProvider")
  return context
}

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAppContext()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

// Main layout with sidebar
function MainLayout({ children }: { children: React.ReactNode }) {
  const {
    subjects,
    selectedSubject,
    setSelectedSubject,
    units,
    userProfile,
    user,
    setUser,
    loadSubjects,
    theme,
    toggleTheme,
    showUploadModal,
    setShowUploadModal,
    isSidebarOpen,
    setIsSidebarOpen,
  } = useAppContext()
  const navigate = useNavigate()
  const location = useLocation()

  function handleSelectTopic(topic: Topic) {
    navigate(`/topic/${topic.id}/notes`)
  }

  function handleUploadSuccess(result: { subject?: Subject }) {
    loadSubjects()
    if (result.subject) setSelectedSubject(result.subject)
  }

  async function handleDeleteSubject(subjectId: number) {
    if (!confirm("Delete this subject and all its content?")) return
    await api.delete("/subjects/" + subjectId + "/delete_with_content/")
    setSelectedSubject(null)
    loadSubjects()
    navigate("/dashboard")
  }

  function handleLogout() {
    localStorage.removeItem("token")
    localStorage.removeItem("neon_access_token")
    localStorage.removeItem("auth_provider")
    localStorage.removeItem("user")
    setUser(null)
    navigate("/login")
  }

  // Get current tab from route
  const getActiveTab = () => {
    const path = location.pathname
    if (path.includes("/notes")) return "notes"
    if (path.includes("/mindmap")) return "mindmap"
    if (path.includes("/flashcards")) return "flashcards"
    if (path.includes("/mcqs")) return "mcqs"
    if (path.includes("/chat")) return "chat"
    if (path.includes("/settings")) return "settings"
    if (path.includes("/about")) return "about"
    return "dashboard"
  }

  const activeTab = getActiveTab()
  const topicId = location.pathname.match(/\/topic\/(\d+)/)?.[1]

  return (
    <div className="min-h-screen bg-background transition-colors duration-300">
      <Sidebar
        subjects={subjects}
        selectedSubject={selectedSubject}
        onSelectSubject={setSelectedSubject}
        units={units}
        selectedTopic={null}
        onSelectTopic={handleSelectTopic}
        onUploadClick={() => setShowUploadModal(true)}
        onDeleteSubject={handleDeleteSubject}
        user={user}
        onLogout={handleLogout}
        onSettingsClick={() => navigate("/settings")}
        onAboutClick={() => navigate("/about")}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <SyllabusUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onSuccess={handleUploadSuccess}
      />

      <div className="lg:ml-72 min-h-screen pb-24 md:pb-8 transition-all duration-300">
        {/* Top Bar */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="sticky top-0 z-30 flex justify-between items-center p-3 md:p-4 mx-2 md:mx-4 mt-2 md:mt-4 mb-4 md:mb-8 bg-card/80 backdrop-blur-lg rounded-2xl shadow-sm border"
        >
          <div className="flex items-center gap-3 min-w-0">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden flex-shrink-0 active:scale-90 transition-transform"
              aria-label="Open sidebar"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="min-w-0">
              <h1 className="text-lg md:text-2xl font-bold truncate">
                {selectedSubject ? selectedSubject.name : "Welcome"}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-1 md:gap-4 flex-shrink-0">
            <motion.div whileTap={{ scale: 0.9, rotate: 15 }}>
              <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}>
                {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
            </motion.div>
          </div>
        </motion.div>

        <div className="px-3 md:px-8">
          {/* Usage Warning */}
          <AnimatePresence>
            {userProfile && !userProfile.has_api_key && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
              >
                <Card className="bg-yellow-500/10 border-l-4 border-yellow-500 mb-4 md:mb-6 interactive-card">
                  <CardContent className="p-3 md:p-4 flex items-start md:items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5 md:mt-0" />
                    <p className="text-xs md:text-sm">
                      <strong>Note:</strong> Using shared quota ({userProfile.daily_usage}/3 topics).{" "}
                      <button
                        onClick={() => navigate("/settings")}
                        className="font-semibold underline hover:text-yellow-600"
                      >
                        Add Gemini API Key
                      </button>
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Main Content */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="page-transition min-h-[500px]"
          >
            {children}
          </motion.div>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav
        activeTab={activeTab}
        onTabChange={(tab) => {
          if (topicId) {
            navigate(`/topic/${topicId}/${tab}`)
          } else if (tab === "dashboard") {
            navigate("/dashboard")
          }
        }}
        onMenuClick={() => setIsSidebarOpen(true)}
        hasSelectedTopic={!!topicId}
      />

      {/* Floating Action Button for mobile */}
      {subjects.length > 0 && !topicId && activeTab === "dashboard" && (
        <FloatingActionButton
          onClick={() => setShowUploadModal(true)}
          icon={Plus}
          label="Add Subject"
        />
      )}
    </div>
  )
}

// Topic page with tabs
function TopicPage() {
  const { topicId, tab = "notes" } = useParams<{ topicId: string; tab: string }>()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const { selectedSubject } = useAppContext()
  const [topic, setTopic] = useState<Topic | null>(null)
  const [notes, setNotes] = useState<Note | null>(null)
  const [mindmap, setMindmap] = useState<Mindmap | null>(null)
  const [flashcards, setFlashcards] = useState<Flashcard[]>([])
  const [mcqs, setMcqs] = useState<MCQ[]>([])

  useEffect(() => {
    if (topicId) {
      api.get<Topic>(`/topics/${topicId}/`).then(setTopic).catch(console.error)
    }
  }, [topicId])

  useEffect(() => {
    // Reset content when topic changes
    setNotes(null)
    setMindmap(null)
    setFlashcards([])
    setMcqs([])
  }, [topicId])

  // Timer logic for study time
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>
    if (topic) {
      interval = setInterval(() => {
        api
          .post("/progress/update_activity/", {
            topic_id: topic.id,
            activity_type: "time",
            duration: 60,
          })
          .catch(console.error)
      }, 60000)
    }
    return () => clearInterval(interval)
  }, [topic])

  async function handleCompleteTopic(force = false) {
    if (!topic) return
    try {
      const res = await api.post<{
        status?: string
        warnings?: string[]
        message?: string
      }>("/progress/mark_complete/", {
        topic_id: topic.id,
        confirm: force,
      })
      if (res.status === "warning") {
        if (confirm((res.warnings?.join("\n") || "") + "\n\n" + res.message)) {
          handleCompleteTopic(true)
        }
      } else {
        showToast("🎉 Topic marked as complete!", "success")
      }
    } catch {
      showToast("Failed to mark complete", "error")
    }
  }

  const tabs = [
    { id: "notes", label: "Notes", icon: BookOpen },
    { id: "mindmap", label: "Mindmap", icon: Network },
    { id: "flashcards", label: "Flashcards", icon: Copy },
    { id: "mcqs", label: "MCQs", icon: HelpCircle },
    { id: "chat", label: "Ask Doubt", icon: Bot },
  ]

  if (!topicId) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div>
      {/* Topic Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl md:text-2xl font-bold">{topic?.name || "Loading..."}</h2>
          <p className="text-muted-foreground text-sm">{selectedSubject?.name}</p>
        </div>
        <Button
          variant="success"
          onClick={() => handleCompleteTopic(false)}
          className="hidden md:flex"
        >
          <CheckCircle2 className="h-4 w-4 mr-2" /> Complete
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="hidden md:block mb-6 bg-card p-2 rounded-xl shadow-sm border overflow-x-auto">
        <div className="flex gap-2 min-w-max">
          {tabs.map((t) => (
            <motion.div key={t.id} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                variant={tab === t.id ? "default" : "ghost"}
                size="sm"
                onClick={() => navigate(`/topic/${topicId}/${t.id}`)}
                className={cn("gap-2 transition-all", tab === t.id && "shadow-md")}
              >
                <t.icon className="h-4 w-4" />
                {t.label}
              </Button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {tab === "notes" && (
            <NotesTab topicId={parseInt(topicId)} notes={notes} setNotes={setNotes} />
          )}
          {tab === "mindmap" && (
            <MindmapTab topicId={parseInt(topicId)} mindmap={mindmap} setMindmap={setMindmap} />
          )}
          {tab === "flashcards" && (
            <FlashcardsTab
              topicId={parseInt(topicId)}
              flashcards={flashcards}
              setFlashcards={setFlashcards}
            />
          )}
          {tab === "mcqs" && (
            <MCQTab topicId={parseInt(topicId)} mcqs={mcqs} setMcqs={setMcqs} />
          )}
          {tab === "chat" && (
            <ChatTab topicId={parseInt(topicId)} topicName={topic?.name || ""} />
          )}
        </motion.div>
      </AnimatePresence>

      {/* Mobile Complete Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => handleCompleteTopic(false)}
        className="md:hidden fixed bottom-24 right-4 z-40 bg-success text-white p-3 rounded-full shadow-lg shadow-success/30"
      >
        <CheckCircle2 className="h-6 w-6" />
      </motion.button>
    </div>
  )
}

// Dashboard page
function DashboardPage() {
  const { selectedSubject, subjects, setShowUploadModal } = useAppContext()

  if (subjects.length === 0) {
    return <WelcomeScreen onUploadClick={() => setShowUploadModal(true)} />
  }

  return <Dashboard subjectId={selectedSubject?.id} />
}

// Main App Provider
function AppProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null)
  const [units, setUnits] = useState<Unit[]>([])
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [theme, setTheme] = useState<"light" | "dark">("light")
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  // Apply theme
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  // Check auth on mount
  useEffect(() => {
    const init = async () => {
      const neonToken = localStorage.getItem("neon_access_token")
      const token = localStorage.getItem("token")
      const savedUser = localStorage.getItem("user")

      if (neonToken) {
        try {
          const profile = await api.get<User>("/auth/profile/")
          if (profile && profile.id) {
            localStorage.setItem("user", JSON.stringify(profile))
            setUser(profile)
          }
        } catch {
          localStorage.removeItem("neon_access_token")
          localStorage.removeItem("auth_provider")
        }
      } else if (token && savedUser) {
        setUser(JSON.parse(savedUser))
      }

      const savedTheme = localStorage.getItem("theme") as "light" | "dark" | null
      if (savedTheme) setTheme(savedTheme)
      setAuthChecked(true)
    }

    init()
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light"
    setTheme(newTheme)
    localStorage.setItem("theme", newTheme)
  }

  useEffect(() => {
    if (user) {
      api.get<UserProfile>("/auth/profile/").then(setUserProfile).catch(console.error)
    }
  }, [user])

  useEffect(() => {
    if (user) loadSubjects()
  }, [user])

  useEffect(() => {
    if (selectedSubject) {
      api.get<Subject>("/subjects/" + selectedSubject.id + "/").then((data) => {
        setUnits(data.units || [])
      })
    } else {
      setUnits([])
    }
  }, [selectedSubject])

  async function loadSubjects() {
    const data = await api.get<Subject[]>("/subjects/")
    setSubjects(Array.isArray(data) ? data : [])
  }

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading message="Loading..." />
      </div>
    )
  }

  const contextValue: AppContextType = {
    user,
    setUser,
    subjects,
    loadSubjects,
    selectedSubject,
    setSelectedSubject,
    units,
    setUnits,
    userProfile,
    theme,
    toggleTheme,
    showUploadModal,
    setShowUploadModal,
    isSidebarOpen,
    setIsSidebarOpen,
  }

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>
}

// Auth pages wrapper
function AuthWrapper() {
  const { user, setUser } = useAppContext()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    if (user) {
      const from = (location.state as { from?: Location })?.from?.pathname || "/dashboard"
      navigate(from, { replace: true })
    }
  }, [user, navigate, location])

  if (user) return null

  return <AuthPage onLogin={setUser} />
}

function AppRoutes() {
  return (
    <Routes>
      {/* Auth routes */}
      <Route path="/login" element={<AuthWrapper />} />
      <Route path="/register" element={<AuthWrapper />} />
      <Route path="/verify-email" element={<AuthWrapper />} />
      <Route path="/forgot-password" element={<AuthWrapper />} />
      <Route path="/reset-password" element={<AuthWrapper />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Navigate to="/dashboard" replace />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <MainLayout>
              <DashboardPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/topic/:topicId/:tab?"
        element={
          <ProtectedRoute>
            <MainLayout>
              <TopicPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <MainLayout>
              <SettingsTab />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/about"
        element={
          <ProtectedRoute>
            <MainLayout>
              <AboutTab />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppProvider>
          <AppRoutes />
        </AppProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
