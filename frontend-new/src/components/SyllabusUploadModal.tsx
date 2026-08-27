import { useState } from "react"
import { motion } from "framer-motion"
import { Upload, Sparkles, Lightbulb, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { api } from "@/lib/api"

interface SyllabusUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (result: any) => void
}

export function SyllabusUploadModal({ isOpen, onClose, onSuccess }: SyllabusUploadModalProps) {
  const [subjectName, setSubjectName] = useState("")
  const [syllabusText, setSyllabusText] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!subjectName.trim() || !syllabusText.trim()) {
      setError("Please fill in both fields")
      return
    }
    setLoading(true)
    setError("")
    try {
      const result = await api.post<any>("/subjects/upload_syllabus/", {
        subject_name: subjectName,
        syllabus_text: syllabusText,
      })
      if (result.error) {
        setError(result.error)
      } else {
        onSuccess(result)
        setSubjectName("")
        setSyllabusText("")
        onClose()
      }
    } catch {
      setError("Failed to upload syllabus. Please try again.")
    }
    setLoading(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader className="bg-gradient-to-r from-primary to-blue-600 -m-6 mb-0 p-6 rounded-t-2xl">
          <DialogTitle className="text-white flex items-center gap-2 text-xl">
            <Upload className="h-5 w-5" /> Upload Syllabus
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
          <div>
            <label htmlFor="subject-name" className="block text-sm font-semibold mb-2">
              Subject Name <span className="text-destructive">*</span>
            </label>
            <Input
              id="subject-name"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
              placeholder="e.g., Data Structures, Art History"
            />
          </div>

          <div>
            <label htmlFor="syllabus-content" className="block text-sm font-semibold mb-2">
              Syllabus Content <span className="text-destructive">*</span>
            </label>
            <Textarea
              id="syllabus-content"
              value={syllabusText}
              onChange={(e) => setSyllabusText(e.target.value)}
              placeholder="Paste your syllabus text here from PDF, Word, or Website..."
              rows={12}
              className="font-mono text-sm"
            />
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-destructive/10 text-destructive rounded-lg border border-destructive/20"
            >
              {error}
            </motion.div>
          )}

          <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
            <h4 className="font-semibold text-primary mb-2 flex items-center text-sm">
              <Lightbulb className="h-4 w-4 mr-2" /> Pro Tips
            </h4>
            <ul className="text-sm text-muted-foreground space-y-1 ml-6 list-disc">
              <li>Copy and paste your syllabus directly from PDF or document.</li>
              <li>Ensure unit names and topics are clearly visible text.</li>
            </ul>
          </div>

          <div className="flex gap-3 pt-4 border-t">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading} variant="gradient" className="flex-1">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Processing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" /> Generate Course
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
