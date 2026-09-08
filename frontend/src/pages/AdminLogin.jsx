import { useState } from 'react'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function AdminLogin() {
  const { isAuthenticated, loading, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="skeleton w-56 h-8 rounded-xl" />
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/admin" replace />

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await login(email, password)
      toast.success('مرحباً بك في استوديو الإبداع! 🎒🎨')
      navigate('/admin')
    } catch (err) {
      const status = err?.response?.status
      if (status === 429) {
        toast.error('محاولات كثيرة. انتظري بضع دقائق.')
      } else {
        toast.error('البريد الإلكتروني أو كلمة المرور غير صحيحة!')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center p-4 relative z-10 w-full">
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-white/95 backdrop-blur-xl rounded-3xl p-10 w-full max-w-[420px] shadow-xl border-2 border-slate-200/90 text-center"
      >
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-pastel-yellow to-pastel-pink flex items-center justify-center text-3xl mx-auto mb-4 shadow-lg">
          🔑
        </div>

        <h2 className="m-0 mb-1 text-2xl font-extrabold text-text-dark">
          المدخل السري للاستوديو
        </h2>
        <p className="m-0 mb-6 text-sm text-text-muted">
          أدخلي بياناتك لتثبيت رسومات وتسجيلات وإنجازات جديدة!
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 text-right">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">البريد الإلكتروني</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="teacher@schoolboard.local"
              className="w-full px-4 py-2.5 rounded-2xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500 transition-all"
              style={{ fontFamily: 'var(--font-cairo)' }}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">كلمة المرور</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full px-4 py-2.5 rounded-2xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500 transition-all"
              style={{ fontFamily: 'var(--font-cairo)' }}
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 mt-1 rounded-full bg-gradient-to-l from-purple-500 to-pink-500 text-white font-bold text-base border-none cursor-pointer shadow-lg transition-all hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-70"
          >
            {submitting ? 'جاري الدخول...' : 'افتحي استوديو الإبداع ✨'}
          </button>
        </form>

        <div className="mt-5">
          <Link to="/" className="text-sm text-purple-500 font-bold no-underline hover:underline">
            الرجوع إلى حائط إنجازاتي ←
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
