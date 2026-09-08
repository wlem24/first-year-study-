import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { updateProfile } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function SettingsModal({ isOpen, onClose }) {
  const { admin, refreshUser } = useAuth()
  const [email, setEmail] = useState(admin?.email || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const data = {}
      if (email !== admin?.email) data.email = email
      if (newPassword) {
        data.current_password = currentPassword
        data.new_password = newPassword
      }

      if (Object.keys(data).length === 0) {
        toast('لم يتم إجراء أي تغييرات', { icon: 'ℹ️' })
        return
      }

      await updateProfile(data)
      if (refreshUser) await refreshUser()
      toast.success('تم تحديث البيانات بنجاح! ✨')
      onClose()
      setCurrentPassword('')
      setNewPassword('')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'حدث خطأ أثناء التحديث')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        initial={{ scale: 0.95, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 20 }}
        className="relative bg-white/95 backdrop-blur-xl rounded-3xl w-full max-w-md shadow-2xl border border-slate-100 overflow-hidden"
      >
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="m-0 text-xl font-bold text-text-dark">إعدادات الحساب ⚙️</h3>
            <button onClick={onClose} className="w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center border-none cursor-pointer hover:bg-slate-200 transition-colors">
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4 text-right">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">البريد الإلكتروني</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-2xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500 transition-all"
                dir="ltr"
              />
            </div>
            
            <div className="border-t-2 border-slate-100 my-2 pt-4">
              <h4 className="text-sm font-bold text-slate-800 mb-4">تغيير كلمة المرور (اختياري)</h4>
              
              <div className="mb-4">
                <label className="block text-xs font-bold text-slate-700 mb-1">كلمة المرور الحالية</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500 transition-all"
                  placeholder="أدخل كلمة المرور الحالية"
                  dir="ltr"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">كلمة المرور الجديدة</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500 transition-all"
                  placeholder="أدخل كلمة المرور الجديدة"
                  dir="ltr"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 mt-4 rounded-xl bg-gradient-to-l from-purple-500 to-pink-500 text-white font-bold text-base border-none cursor-pointer shadow-md hover:shadow-lg transition-all disabled:opacity-70"
            >
              {submitting ? 'جاري الحفظ...' : 'حفظ التغييرات ✔️'}
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  )
}
