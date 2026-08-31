import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Bot, Send, MessageCircle, Loader2, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import type { ChatMessage } from "@/lib/api"
import { cn } from "@/lib/utils"

interface ChatTabProps {
  topicId: number
  topicName: string
}

export function ChatTab({ topicId, topicName }: ChatTabProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  async function handleSend() {
    if (!input.trim()) return
    const userMessage = input
    setMessages((prev) => [...prev, { role: "user", content: userMessage }])
    setInput("")
    setLoading(true)
    try {
      const res = await api.post<{ ai_response: string }>("/chat/", {
        topic_id: topicId,
        message: userMessage,
      })
      setMessages((prev) => [...prev, { role: "ai", content: res.ai_response }])
    } catch {
      setMessages((prev) => [...prev, { role: "ai", content: "Sorry, I encountered an error." }])
    }
    setLoading(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <Card className="h-[650px] flex flex-col overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-primary to-blue-600 text-white rounded-t-xl">
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" /> AI Tutor
          </CardTitle>
          <p className="text-xs text-blue-100 opacity-90 truncate max-w-md">
            Discussing: {topicName}
          </p>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-6 space-y-6 bg-muted/30">
          {messages.length === 0 && (
            <div className="text-center py-12 opacity-50">
              <div className="w-20 h-20 bg-card border-2 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="h-10 w-10 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium">Start a conversation!</h3>
              <p className="text-sm text-muted-foreground">Ask any question about this topic.</p>
            </div>
          )}

          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
              >
                <div
                  className={cn(
                    "max-w-[85%] p-4 rounded-2xl shadow-sm flex gap-3",
                    msg.role === "user"
                      ? "bg-primary text-white rounded-br-none"
                      : "bg-card border rounded-bl-none"
                  )}
                >
                  {msg.role === "ai" && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  )}
                  <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-card border p-4 rounded-2xl rounded-bl-none shadow-sm flex items-center gap-3">
                <div className="flex space-x-1">
                  <motion.div
                    className="w-2 h-2 bg-primary/40 rounded-full"
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-primary/40 rounded-full"
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.1 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-primary/40 rounded-full"
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                  />
                </div>
                <span className="text-sm text-muted-foreground font-medium">AI is thinking...</span>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </CardContent>

        <div className="p-4 bg-card border-t">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type your question..."
              className="shadow-inner"
            />
            <Button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              size="icon"
              className="px-6"
              aria-label="Send message"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}
