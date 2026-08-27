import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Save, Key, ArrowDown, ArrowUp, Tag, CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { api } from "@/lib/api"
import type { UserProfile } from "@/lib/api"

export function SettingsTab() {
  const [apiKey, setApiKey] = useState("")
  const [status, setStatus] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")

  useEffect(() => {
    loadProfile()
  }, [])

  async function loadProfile() {
    try {
      const data = await api.get<UserProfile>("/auth/profile/")
      setStatus(data)
      if (data.api_key) setApiKey(data.api_key)
    } catch (err) {
      console.error(err)
    }
  }

  async function handleSave() {
    setLoading(true)
    setMessage("")
    try {
      const res = await api.post<{ has_api_key: boolean }>("/auth/update_api_key/", {
        api_key: apiKey,
      })
      setStatus((prev) => prev && { ...prev, has_api_key: res.has_api_key })
      setMessage("Settings saved successfully!")
      setTimeout(() => setMessage(""), 3000)
    } catch {
      setMessage("Failed to save settings.")
    }
    setLoading(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl mx-auto space-y-6"
    >
      <h2 className="text-2xl font-bold">Settings</h2>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" /> Gemini API Configuration
          </CardTitle>
          <CardDescription>
            By default, you can generate content for 3 topics per day. To remove this limit, provide
            your own Google Gemini API Key.{" "}
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              className="text-primary hover:underline"
            >
              Get a key here
            </a>
            .
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="api-key-input" className="block text-sm font-medium mb-1">Your API Key</label>
            <div className="flex gap-2">
              <Input
                id="api-key-input"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="AIzaSy..."
                className="flex-1"
              />
              <Button onClick={handleSave} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save
              </Button>
            </div>
          </div>

          {message && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-3 rounded-lg text-sm flex items-center gap-2 ${
                message.includes("Failed")
                  ? "bg-destructive/10 text-destructive"
                  : "bg-green-500/10 text-green-500"
              }`}
            >
              {message.includes("Failed") ? (
                <XCircle className="h-4 w-4" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )}
              {message}
            </motion.div>
          )}
        </CardContent>
      </Card>

      {status && (
        <Card>
          <CardHeader>
            <CardTitle>Account Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm text-muted-foreground">Current Plan</p>
                <p
                  className={`font-semibold ${status.has_api_key ? "text-green-500" : "text-yellow-500"}`}
                >
                  {status.has_api_key ? "Unlimited (Custom Key)" : "Free Tier (Limited)"}
                </p>
              </div>
              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm text-muted-foreground">Daily Quota Usage</p>
                <p className="font-semibold">{status.daily_usage} / 3 topics</p>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-4">Token Usage & Estimated Cost</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-muted p-4 rounded-lg border hover:border-blue-400 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <ArrowDown className="h-4 w-4 text-blue-500" />
                    <p className="text-sm text-muted-foreground font-medium">Input Tokens</p>
                  </div>
                  <p className="text-2xl font-bold">
                    {status.total_input_tokens?.toLocaleString() || 0}
                  </p>
                </motion.div>
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-muted p-4 rounded-lg border hover:border-green-400 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <ArrowUp className="h-4 w-4 text-green-500" />
                    <p className="text-sm text-muted-foreground font-medium">Output Tokens</p>
                  </div>
                  <p className="text-2xl font-bold">
                    {status.total_output_tokens?.toLocaleString() || 0}
                  </p>
                </motion.div>
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-muted p-4 rounded-lg border hover:border-purple-400 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Tag className="h-4 w-4 text-purple-500" />
                    <p className="text-sm text-muted-foreground font-medium">Est. Cost (USD)</p>
                  </div>
                  <p className="text-2xl font-bold">${status.estimated_cost?.toFixed(4) || "0.0000"}</p>
                </motion.div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                * Cost estimation based on standard market rates ($0.10/1M input, $0.40/1M output).
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  )
}
