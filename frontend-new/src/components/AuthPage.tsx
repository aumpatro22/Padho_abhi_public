import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { GraduationCap, Eye, EyeOff, Loader2, Mail, CheckCircle, ArrowLeft, KeyRound } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import type { User } from "@/lib/api"

type AuthView = 'login' | 'register' | 'verify-pending' | 'verify-email' | 'forgot-password' | 'reset-password'

interface AuthPageProps {
  onLogin: (user: User) => void
}

export function AuthPage({ onLogin }: AuthPageProps) {
  const [view, setView] = useState<AuthView>('login')
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)
  const [neonToken, setNeonToken] = useState("")
  const [neonError, setNeonError] = useState("")
  const [neonLoading, setNeonLoading] = useState(false)
  const [pendingEmail, setPendingEmail] = useState("")
  const [verificationToken, setVerificationToken] = useState("")

  // Check for verification token in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const type = params.get('type') || (window.location.pathname.includes('reset-password') ? 'reset' : 'verify')
    
    if (token) {
      setVerificationToken(token)
      if (type === 'reset' || window.location.pathname.includes('reset-password')) {
        setView('reset-password')
      } else {
        setView('verify-email')
        handleVerifyEmail(token)
      }
    }
  }, [])

  async function handleVerifyEmail(token: string) {
    setLoading(true)
    setError("")
    try {
      const res = await fetch("/api/auth/verify_email/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      })
      const data = await res.json()
      if (res.ok && data.token) {
        setSuccess("Email verified successfully! Logging you in...")
        localStorage.setItem("token", data.token)
        localStorage.setItem("user", JSON.stringify(data.user))
        localStorage.setItem("auth_provider", "django")
        setTimeout(() => onLogin(data.user), 1500)
      } else {
        setError(data.error || "Verification failed")
      }
    } catch {
      setError("Connection error. Please try again.")
    }
    setLoading(false)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    
    try {
      if (view === 'register') {
        if (password !== confirmPassword) {
          setError("Passwords do not match")
          setLoading(false)
          return
        }
        if (password.length < 8) {
          setError("Password must be at least 8 characters")
          setLoading(false)
          return
        }
        
        const res = await fetch("/api/auth/register/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, email, password }),
        })
        const data = await res.json()
        
        if (data.requires_verification) {
          setPendingEmail(data.email || email)
          setView('verify-pending')
        } else if (data.token) {
          localStorage.setItem("auth_provider", "django")
          localStorage.setItem("token", data.token)
          localStorage.setItem("user", JSON.stringify(data.user))
          onLogin(data.user)
        } else {
          setError(data.error || data.detail || "Registration failed")
        }
      } else if (view === 'login') {
        const res = await fetch("/api/auth/login/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        })
        const data = await res.json()
        
        if (data.requires_verification) {
          setPendingEmail(data.email || "")
          setView('verify-pending')
        } else if (data.token) {
          localStorage.removeItem("neon_access_token")
          localStorage.setItem("auth_provider", "django")
          localStorage.setItem("token", data.token)
          localStorage.setItem("user", JSON.stringify(data.user))
          onLogin(data.user)
        } else {
          setError(data.error || data.detail || "Authentication failed")
        }
      }
    } catch {
      setError("Connection error. Please try again.")
    }
    setLoading(false)
  }

  async function handleResendVerification() {
    setLoading(true)
    setError("")
    try {
      const res = await fetch("/api/auth/resend_verification/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: pendingEmail }),
      })
      const data = await res.json()
      if (res.ok) {
        setSuccess("Verification email sent!")
      } else {
        setError(data.error || "Failed to resend email")
      }
    } catch {
      setError("Connection error. Please try again.")
    }
    setLoading(false)
  }

  async function handleForgotPassword(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")
    try {
      const res = await fetch("/api/auth/forgot_password/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })
      const data = await res.json()
      if (res.ok) {
        setSuccess(data.message || "If an account exists, you will receive a reset email.")
      } else {
        setError(data.error || "Failed to send reset email")
      }
    } catch {
      setError("Connection error. Please try again.")
    }
    setLoading(false)
  }

  async function handleResetPassword(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")
    
    if (password !== confirmPassword) {
      setError("Passwords do not match")
      setLoading(false)
      return
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters")
      setLoading(false)
      return
    }
    
    try {
      const res = await fetch("/api/auth/reset_password/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: verificationToken, password }),
      })
      const data = await res.json()
      if (res.ok) {
        setSuccess("Password reset successfully! You can now login.")
        setTimeout(() => {
          setView('login')
          setPassword("")
          setConfirmPassword("")
          window.history.replaceState({}, '', window.location.pathname)
        }, 2000)
      } else {
        setError(data.error || "Failed to reset password")
      }
    } catch {
      setError("Connection error. Please try again.")
    }
    setLoading(false)
  }

  async function handleNeonTokenLogin(e: React.FormEvent) {
    e.preventDefault()
    setNeonError("")
    if (!neonToken.trim()) {
      setNeonError("Please paste a Neon Auth access token")
      return
    }
    setNeonLoading(true)
    try {
      localStorage.setItem("neon_access_token", neonToken.trim())
      localStorage.setItem("auth_provider", "neon")
      localStorage.removeItem("token")
      const profile = await api.get<User>("/auth/profile/")
      if (profile && profile.id) {
        localStorage.setItem("user", JSON.stringify(profile))
        onLogin(profile)
      } else {
        throw new Error("Invalid Neon Auth token")
      }
    } catch (err) {
      localStorage.removeItem("neon_access_token")
      localStorage.removeItem("auth_provider")
      setNeonError(err instanceof Error ? err.message : "Neon Auth token invalid")
    }
    setNeonLoading(false)
  }

  // Verify Email Pending Screen
  if (view === 'verify-pending') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary via-purple-500 to-pink-500 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
        >
          <Card className="w-full max-w-md shadow-2xl border-0">
            <CardHeader className="text-center pb-4">
              <motion.div
                className="w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg"
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Mail className="h-10 w-10 text-white" />
              </motion.div>
              <CardTitle className="text-2xl font-bold">Check Your Email</CardTitle>
              <CardDescription>
                We've sent a verification link to
              </CardDescription>
              <p className="text-primary font-semibold mt-2">{pendingEmail}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-muted p-4 rounded-lg text-sm text-muted-foreground">
                <p>Click the link in the email to verify your account and start learning!</p>
                <p className="mt-2">The link will expire in 24 hours.</p>
              </div>
              
              <AnimatePresence>
                {success && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-3 bg-green-100 text-green-700 rounded-lg text-sm"
                  >
                    {success}
                  </motion.div>
                )}
                {error && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm"
                  >
                    {error}
                  </motion.div>
                )}
              </AnimatePresence>
              
              <Button
                variant="outline"
                className="w-full"
                onClick={handleResendVerification}
                disabled={loading}
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Resend Verification Email
              </Button>
              
              <Button
                variant="ghost"
                className="w-full"
                onClick={() => {
                  setView('login')
                  setError("")
                  setSuccess("")
                }}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Login
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  // Verify Email Screen (from link)
  if (view === 'verify-email') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary via-purple-500 to-pink-500 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
        >
          <Card className="w-full max-w-md shadow-2xl border-0">
            <CardHeader className="text-center pb-4">
              <motion.div
                className={`w-20 h-20 ${success ? 'bg-gradient-to-r from-green-500 to-emerald-600' : error ? 'bg-gradient-to-r from-red-500 to-rose-600' : 'bg-gradient-to-r from-primary to-purple-600'} rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg`}
              >
                {loading ? (
                  <Loader2 className="h-10 w-10 text-white animate-spin" />
                ) : success ? (
                  <CheckCircle className="h-10 w-10 text-white" />
                ) : (
                  <Mail className="h-10 w-10 text-white" />
                )}
              </motion.div>
              <CardTitle className="text-2xl font-bold">
                {loading ? "Verifying..." : success ? "Email Verified!" : "Verification Failed"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <AnimatePresence>
                {success && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-4 bg-green-100 text-green-700 rounded-lg text-center"
                  >
                    {success}
                  </motion.div>
                )}
                {error && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-4 bg-destructive/10 text-destructive rounded-lg text-center"
                  >
                    {error}
                  </motion.div>
                )}
              </AnimatePresence>
              
              {!loading && !success && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setView('login')
                    window.history.replaceState({}, '', window.location.pathname)
                  }}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Login
                </Button>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  // Forgot Password Screen
  if (view === 'forgot-password') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary via-purple-500 to-pink-500 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
        >
          <Card className="w-full max-w-md shadow-2xl border-0">
            <CardHeader className="text-center pb-4">
              <motion.div
                className="w-20 h-20 bg-gradient-to-r from-amber-500 to-orange-600 rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg"
              >
                <KeyRound className="h-10 w-10 text-white" />
              </motion.div>
              <CardTitle className="text-2xl font-bold">Forgot Password?</CardTitle>
              <CardDescription>
                Enter your email and we'll send you a reset link
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleForgotPassword} className="space-y-4">
                <div>
                  <label htmlFor="forgot-email" className="block text-sm font-medium mb-1">Email</label>
                  <Input
                    id="forgot-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                  />
                </div>
                
                <AnimatePresence>
                  {success && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="p-3 bg-green-100 text-green-700 rounded-lg text-sm"
                    >
                      {success}
                    </motion.div>
                  )}
                  {error && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm"
                    >
                      {error}
                    </motion.div>
                  )}
                </AnimatePresence>
                
                <Button type="submit" variant="gradient" className="w-full" disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Send Reset Link
                </Button>
              </form>
              
              <Button
                variant="ghost"
                className="w-full"
                onClick={() => {
                  setView('login')
                  setError("")
                  setSuccess("")
                }}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Login
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  // Reset Password Screen
  if (view === 'reset-password') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary via-purple-500 to-pink-500 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
        >
          <Card className="w-full max-w-md shadow-2xl border-0">
            <CardHeader className="text-center pb-4">
              <motion.div
                className="w-20 h-20 bg-gradient-to-r from-amber-500 to-orange-600 rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg"
              >
                <KeyRound className="h-10 w-10 text-white" />
              </motion.div>
              <CardTitle className="text-2xl font-bold">Reset Password</CardTitle>
              <CardDescription>
                Enter your new password
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleResetPassword} className="space-y-4">
                <div>
                  <label htmlFor="reset-password" className="block text-sm font-medium mb-1">New Password</label>
                  <Input
                    id="reset-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter new password"
                    required
                    minLength={8}
                  />
                </div>
                <div>
                  <label htmlFor="reset-confirm-password" className="block text-sm font-medium mb-1">Confirm Password</label>
                  <Input
                    id="reset-confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    required
                  />
                </div>
                
                <AnimatePresence>
                  {success && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="p-3 bg-green-100 text-green-700 rounded-lg text-sm"
                    >
                      {success}
                    </motion.div>
                  )}
                  {error && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm"
                    >
                      {error}
                    </motion.div>
                  )}
                </AnimatePresence>
                
                <Button type="submit" variant="gradient" className="w-full" disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Reset Password
                </Button>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  const isLogin = view === 'login'

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary via-purple-500 to-pink-500 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <Card className="w-full max-w-md shadow-2xl border-0">
          <CardHeader className="text-center pb-4">
            <motion.div
              className="w-20 h-20 bg-gradient-to-r from-primary to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg"
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              <GraduationCap className="h-10 w-10 text-white" />
            </motion.div>
            <CardTitle className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">
              Padho Abhi
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              AI-Powered Smart Study Platform
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex bg-muted rounded-lg p-1">
              <Button
                variant={isLogin ? "default" : "ghost"}
                className={`flex-1 ${isLogin ? "" : "text-muted-foreground"}`}
                onClick={() => { setView('login'); setError(""); setSuccess("") }}
              >
                Login
              </Button>
              <Button
                variant={!isLogin ? "default" : "ghost"}
                className={`flex-1 ${!isLogin ? "" : "text-muted-foreground"}`}
                onClick={() => { setView('register'); setError(""); setSuccess("") }}
              >
                Register
              </Button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="auth-username" className="block text-sm font-medium mb-1">Username</label>
                <Input
                  id="auth-username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  required
                />
              </div>
              
              <AnimatePresence mode="wait">
                {!isLogin && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <label htmlFor="auth-email" className="block text-sm font-medium mb-1">Email</label>
                    <Input
                      id="auth-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter email"
                      required={!isLogin}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              <div>
                <label htmlFor="auth-password" className="block text-sm font-medium mb-1">Password</label>
                <div className="relative">
                  <Input
                    id="auth-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    required
                    className="pr-10"
                    minLength={!isLogin ? 8 : undefined}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {!isLogin && (
                  <p className="text-xs text-muted-foreground mt-1">Minimum 8 characters</p>
                )}
              </div>

              <AnimatePresence mode="wait">
                {!isLogin && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <label htmlFor="auth-confirm-password" className="block text-sm font-medium mb-1">Confirm Password</label>
                    <Input
                      id="auth-confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm password"
                      required={!isLogin}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm border border-destructive/20"
                  >
                    {error}
                  </motion.div>
                )}
                {success && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-3 bg-green-100 text-green-700 rounded-lg text-sm border border-green-200"
                  >
                    {success}
                  </motion.div>
                )}
              </AnimatePresence>

              {isLogin && (
                <div className="text-right">
                  <button
                    type="button"
                    onClick={() => { setView('forgot-password'); setError(""); setSuccess("") }}
                    className="text-sm text-primary hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              <Button
                type="submit"
                disabled={loading}
                variant="gradient"
                className="w-full"
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Please wait...
                  </>
                ) : isLogin ? (
                  "Login"
                ) : (
                  "Create Account"
                )}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">or use Neon Auth</span>
              </div>
            </div>

            <form onSubmit={handleNeonTokenLogin} className="space-y-3">
              <Input
                aria-label="Paste Neon Auth token"
                type="password"
                value={neonToken}
                onChange={(e) => setNeonToken(e.target.value)}
                placeholder="Paste Neon Auth token"
              />
              <AnimatePresence>
                {neonError && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm border border-destructive/20"
                  >
                    {neonError}
                  </motion.div>
                )}
              </AnimatePresence>
              <Button type="submit" variant="outline" disabled={neonLoading} className="w-full">
                {neonLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  "Use Neon Auth Token"
                )}
              </Button>
            </form>

            <p className="text-center text-muted-foreground text-sm">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button
                onClick={() => { setView(isLogin ? 'register' : 'login'); setError(""); setSuccess("") }}
                className="text-primary font-semibold hover:underline"
              >
                {isLogin ? "Register" : "Login"}
              </button>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
