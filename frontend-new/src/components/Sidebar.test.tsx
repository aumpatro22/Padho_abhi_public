import { render, screen, fireEvent, cleanup } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { Sidebar } from "./Sidebar"
import type { Subject, Unit, Topic, User } from "@/lib/api"

// Mock PointerEvent / ResizeObserver / scrollIntoView for Radix UI select in JSDOM
if (typeof window !== "undefined") {
  if (!window.PointerEvent) {
    class PointerEvent extends MouseEvent {
      constructor(type: string, params: PointerEventInit = {}) {
        super(type, params)
      }
    }
    window.PointerEvent = PointerEvent as unknown as typeof window.PointerEvent
  }
  if (!window.HTMLElement.prototype.scrollIntoView) {
    window.HTMLElement.prototype.scrollIntoView = () => {}
  }
  if (!window.HTMLElement.prototype.hasPointerCapture) {
    window.HTMLElement.prototype.hasPointerCapture = () => false
  }
  if (!window.HTMLElement.prototype.setPointerCapture) {
    window.HTMLElement.prototype.setPointerCapture = () => {}
  }
  if (!window.HTMLElement.prototype.releasePointerCapture) {
    window.HTMLElement.prototype.releasePointerCapture = () => {}
  }
}

const mockSubjects: Subject[] = [
  { id: 1, name: "Physics", user: 1, created_at: "2025-01-01" },
  { id: 2, name: "Chemistry", user: 1, created_at: "2025-01-01" },
]

const mockUnits: Unit[] = [
  {
    id: 101,
    subject: 1,
    unit_number: 1,
    title: "Thermodynamics",
    topics: [
      { id: 201, unit: 101, name: "First Law", order: 1, has_notes: true, created_at: "2025-01-01" },
      { id: 202, unit: 101, name: "Second Law", order: 2, has_notes: false, created_at: "2025-01-01" },
    ],
  },
]

const mockUser: User = {
  id: 1,
  username: "testuser",
  email: "test@example.com",
}

describe("Sidebar Component", () => {
  let defaultProps: React.ComponentProps<typeof Sidebar>

  beforeEach(() => {
    vi.clearAllMocks()
    defaultProps = {
      subjects: mockSubjects,
      selectedSubject: mockSubjects[0],
      onSelectSubject: vi.fn(),
      units: mockUnits,
      selectedTopic: null as Topic | null,
      onSelectTopic: vi.fn(),
      onUploadClick: vi.fn(),
      onDeleteSubject: vi.fn(),
      user: mockUser,
      onLogout: vi.fn(),
      onSettingsClick: vi.fn(),
      onAboutClick: vi.fn(),
      isOpen: true,
      onClose: vi.fn(),
    }
  })

  afterEach(() => {
    cleanup()
  })

  it("renders header title and branding text", () => {
    render(<Sidebar {...defaultProps} />)
    expect(screen.getByText("Padho Abhi")).toBeTruthy()
    expect(screen.getByText("AI-POWERED LEARNING")).toBeTruthy()
  })

  it("renders user information and responds to settings click when user is present", () => {
    render(<Sidebar {...defaultProps} />)
    expect(screen.getByText("testuser")).toBeTruthy()
    expect(screen.getByText("Free Plan")).toBeTruthy()

    const settingsButton = screen.getByRole("button", { name: "Settings" })
    fireEvent.click(settingsButton)
    expect(defaultProps.onSettingsClick).toHaveBeenCalledTimes(1)
  })

  it("does not render user profile section when user is null", () => {
    render(<Sidebar {...defaultProps} user={null} />)
    expect(screen.queryByText("testuser")).toBeNull()
  })

  it("calls onUploadClick when 'New Subject' button is clicked", () => {
    render(<Sidebar {...defaultProps} />)
    const newSubjectBtn = screen.getByRole("button", { name: /New Subject/i })
    fireEvent.click(newSubjectBtn)
    expect(defaultProps.onUploadClick).toHaveBeenCalledTimes(1)
  })

  it("renders selected subject and triggers onDeleteSubject when Delete Subject is clicked", () => {
    render(<Sidebar {...defaultProps} />)
    const deleteBtn = screen.getByRole("button", { name: /Delete Subject/i })
    expect(deleteBtn).toBeTruthy()

    fireEvent.click(deleteBtn)
    expect(defaultProps.onDeleteSubject).toHaveBeenCalledWith(mockSubjects[0].id)
  })

  it("hides Delete Subject button when selectedSubject is null", () => {
    render(<Sidebar {...defaultProps} selectedSubject={null} />)
    expect(screen.queryByRole("button", { name: /Delete Subject/i })).toBeNull()
  })

  it("calls onAboutClick and onLogout when navigation buttons are clicked", () => {
    render(<Sidebar {...defaultProps} />)

    const aboutBtn = screen.getByRole("button", { name: /About Platform/i })
    fireEvent.click(aboutBtn)
    expect(defaultProps.onAboutClick).toHaveBeenCalledTimes(1)

    const logoutBtn = screen.getByRole("button", { name: /Logout/i })
    fireEvent.click(logoutBtn)
    expect(defaultProps.onLogout).toHaveBeenCalledTimes(1)
  })

  it("expands units and triggers onSelectTopic when topic is clicked", () => {
    render(<Sidebar {...defaultProps} />)

    const unitButton = screen.getByRole("button", { name: /Unit 1/i })
    expect(unitButton).toBeTruthy()

    // Topics shouldn't be visible before clicking unit accordion
    expect(screen.queryByRole("button", { name: /First Law/i })).toBeNull()

    // Click unit to expand
    fireEvent.click(unitButton)
    expect(screen.getByRole("button", { name: /First Law/i })).toBeTruthy()
    expect(screen.getByRole("button", { name: /Second Law/i })).toBeTruthy()

    // Click topic
    const topic1 = screen.getByRole("button", { name: /First Law/i })
    fireEvent.click(topic1)
    expect(defaultProps.onSelectTopic).toHaveBeenCalledWith(mockUnits[0].topics![0])
  })

  it("renders 'No subjects yet' when subjects list is empty", () => {
    render(<Sidebar {...defaultProps} subjects={[]} units={[]} />)
    expect(screen.getByText("No subjects yet")).toBeTruthy()
    expect(screen.getByText("Create one to start!")).toBeTruthy()
  })

  it("renders 'Select a subject to view topics' when subjects exist but units list is empty", () => {
    render(<Sidebar {...defaultProps} units={[]} />)
    expect(screen.getByText("Select a subject to view topics")).toBeTruthy()
  })

  it("calls onClose when close button in header is clicked", () => {
    render(<Sidebar {...defaultProps} isOpen={true} />)

    const closeButton = screen.getByRole("button", { name: /Close sidebar/i })
    fireEvent.click(closeButton)
    expect(defaultProps.onClose).toHaveBeenCalled()
  })
})
