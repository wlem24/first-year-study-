import { useState, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getPosts, deletePost, syncPadlet } from '../services/api'
import UploadForm from '../components/UploadForm'
import StudentUploadModal from '../components/StudentUploadModal'
import SettingsModal from '../components/SettingsModal'

export default function AdminDashboard() {
  const { logout, admin } = useAuth()
  const navigate = useNavigate()
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [editingPost, setEditingPost] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [syncingId, setSyncingId] = useState(null)

  const loadPosts = useCallback(async () => {
    try {
      const data = await getPosts({ page: 1, pageSize: 100 })
      setPosts(data.items || [])
    } catch {
      toast.error('تعذّر تحميل الأنشطة')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadPosts() }, [loadPosts])

  const handleLogout = async () => { await logout(); navigate('/login') }
  const handleCreate = () => { setEditingPost(null); setShowModal(true) }
  const handleEdit = (post) => { setEditingPost(post); setShowModal(true) }
  const handleSaved = () => { setShowModal(false); setEditingPost(null); loadPosts() }

  const handleDelete = async (id) => {
    try {
      await deletePost(id)
      toast.success('تم حذف الإبداع من الحائط')
      setDeleteConfirm(null)
      loadPosts()
    } catch { toast.error('فشل في حذف الإبداع') }
  }

  const handleSyncPadlet = async (id) => {
    setSyncingId(id)
    try {
      await syncPadlet(id)
      toast.success('تم المزامنة مع لوحة بادلت! 📌')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'فشلت المزامنة. تحققي من إعدادات .env')
    } finally { setSyncingId(null) }
  }

  const fiveStarCount = posts.filter((p) => p.star_rating === 5).length
  const audioCount = posts.filter((p) => !!p.audio_url).length

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24">
        {/* شريط الاستوديو */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-6 bg-white/95 rounded-3xl px-6 py-5 backdrop-blur-xl border-2 border-slate-200/90 shadow-sm w-full">
          <div className="flex flex-col sm:flex-row items-center gap-4 text-center sm:text-right">
            <div className="w-14 h-14 flex-shrink-0 rounded-2xl bg-gradient-to-br from-pastel-yellow to-pastel-pink flex items-center justify-center text-3xl shadow-md">
              🎨
            </div>
            <div>
              <h1 className="m-0 text-xl font-extrabold text-text-dark">استوديو ميان الإبداعي ومذكراتي</h1>
              <span className="text-xs text-text-muted mt-1 block">حساب الاستوديو: <strong className="break-all">{admin?.email || 'teacher@schoolboard.local'}</strong></span>
            </div>
          </div>
          <div className="flex flex-wrap justify-center md:justify-end gap-3 w-full md:w-auto">
            <button onClick={() => setShowSettings(true)} className="px-5 py-2.5 rounded-full bg-slate-50 border-2 border-slate-200 text-slate-700 font-bold text-sm cursor-pointer hover:bg-slate-100 transition-all flex items-center justify-center">
              ⚙️ إعدادات
            </button>
            <Link to="/" className="px-5 py-2.5 rounded-full bg-slate-50 border-2 border-slate-200 text-slate-700 no-underline text-sm font-bold hover:bg-slate-100 transition-all flex items-center justify-center">
              👁 شاهدي حائطي
            </Link>
            <button onClick={handleCreate} className="px-5 py-2.5 rounded-full bg-gradient-to-l from-purple-500 to-pink-500 text-white font-bold text-sm border-none cursor-pointer shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center justify-center">
              + ثبّتي إبداعاً جديداً ⭐
            </button>
            <button onClick={handleLogout} className="px-5 py-2.5 rounded-full bg-white border-2 border-slate-200 text-slate-700 font-bold text-sm cursor-pointer hover:bg-slate-50 transition-all flex items-center justify-center">
              خروج
            </button>
          </div>
        </div>

        {/* إحصائيات */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full my-6">
          <div className="bg-pink-50 border-2 border-pink-300 rounded-2xl flex flex-col items-center justify-center p-6 shadow-sm text-center">
            <div className="text-4xl mb-2">📌</div>
            <div className="text-3xl font-extrabold text-pink-800 leading-none">{posts.length}</div>
            <div className="text-sm font-bold text-pink-700 mt-2">إبداعات مثبّتة</div>
          </div>
          <div className="bg-yellow-50 border-2 border-yellow-300 rounded-2xl flex flex-col items-center justify-center p-6 shadow-sm text-center">
            <div className="text-4xl mb-2">⭐</div>
            <div className="text-3xl font-extrabold text-amber-800 leading-none">{fiveStarCount}</div>
            <div className="text-sm font-bold text-amber-700 mt-2">جوائز 5 نجوم</div>
          </div>
          <div className="bg-sky-50 border-2 border-sky-300 rounded-2xl flex flex-col items-center justify-center p-6 shadow-sm text-center">
            <div className="text-4xl mb-2">🎙️</div>
            <div className="text-3xl font-extrabold text-sky-800 leading-none">{audioCount}</div>
            <div className="text-sm font-bold text-sky-700 mt-2">تسجيلات صوتية</div>
          </div>
        </div>

        {/* قائمة الإبداعات */}
        <div className="flex-1 w-full">
          {loading ? (
            <div className="flex flex-col gap-4">
              {[1, 2, 3].map((i) => <div key={i} className="skeleton h-24 rounded-2xl w-full" />)}
            </div>
          ) : posts.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-center border-2 border-dashed border-slate-300 rounded-3xl gap-4 bg-white/80 my-8">
              <div className="text-6xl">🎨</div>
              <div>
                <h3 className="m-0 mb-2 text-xl text-text-dark font-extrabold">استوديوك جاهز للإبداعات!</h3>
                <p className="m-0 text-text-muted text-sm max-w-sm mx-auto leading-relaxed">اضغطي الزر أدناه لرفع صورة لوحة، أو تسجيل قراءة، أو ورقة عمل جديدة وتثبيتها على الحائط.</p>
              </div>
              <button onClick={handleCreate} className="px-8 py-3 mt-2 rounded-full bg-gradient-to-l from-purple-500 to-pink-500 text-white font-bold text-lg border-none cursor-pointer shadow-lg hover:shadow-xl transition-all">
                + ثبّتي أول إبداع
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <AnimatePresence>
                {posts.map((p) => (
                  <motion.div
                    key={p.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="flex flex-col md:flex-row items-start md:items-center gap-4 bg-white/95 rounded-2xl p-5 border-2 border-slate-100 shadow-sm w-full"
                  >
                    <div className="w-16 h-16 rounded-2xl bg-slate-100 overflow-hidden flex-shrink-0 flex items-center justify-center text-3xl">
                      {p.thumbnail_url ? (
                        <img src={p.thumbnail_url} alt="" className="w-full h-full object-cover" />
                      ) : <span>🎨</span>}
                    </div>
                    <div className="flex-1 min-w-0 w-full">
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <span className="px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 text-xs font-bold uppercase whitespace-nowrap border border-purple-100">{p.category}</span>
                        <span className="text-sm whitespace-nowrap">{'⭐'.repeat(p.star_rating || 5)}</span>
                        {p.audio_url && <span className="text-xs bg-sky-50 text-sky-700 border border-sky-200 px-2.5 py-0.5 rounded-full font-bold whitespace-nowrap">🎙️ صوت</span>}
                      </div>
                      <h3 className="m-0 text-base md:text-lg font-bold text-text-dark truncate">{p.title}</h3>
                      {p.teacher_note && <p className="m-0 mt-1 text-xs md:text-sm text-amber-800 truncate">💬 «{p.teacher_note}»</p>}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 w-full md:w-auto mt-2 md:mt-0 justify-end">
                      <button onClick={() => handleSyncPadlet(p.id)} disabled={syncingId === p.id} className="flex-1 md:flex-none px-4 py-2 rounded-xl border-2 border-slate-200 bg-white cursor-pointer text-sm font-bold text-slate-700 hover:bg-slate-50 transition-all flex justify-center items-center">
                        {syncingId === p.id ? '⏳ جاري...' : '📌 مزامنة'}
                      </button>
                      <button onClick={() => handleEdit(p)} className="flex-1 md:flex-none px-4 py-2 rounded-xl border-2 border-slate-200 bg-white cursor-pointer text-sm font-bold text-slate-700 hover:bg-slate-50 transition-all flex justify-center items-center">✏️ تعديل</button>
                      <button onClick={() => setDeleteConfirm(p)} className="px-4 py-2 rounded-xl border-2 border-red-200 bg-red-50 cursor-pointer text-sm font-bold text-red-600 hover:bg-red-100 transition-all flex justify-center items-center">🗑️ حذف</button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      <StudentUploadModal isOpen={showModal} onClose={() => { setShowModal(false); setEditingPost(null) }}>
        <UploadForm post={editingPost} onSaved={handleSaved} />
      </StudentUploadModal>

      {/* نافذة تأكيد الحذف */}
      <AnimatePresence>
        {deleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setDeleteConfirm(null)}
            className="fixed inset-0 z-[2000] flex items-center justify-center bg-slate-900/65 backdrop-blur-sm px-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl p-8 max-w-[420px] w-full text-center shadow-2xl"
            >
              <div className="text-5xl mb-4">⚠️</div>
              <h3 className="m-0 mb-3 text-xl text-text-dark font-extrabold">حذف «{deleteConfirm.title}»؟</h3>
              <p className="text-text-muted text-sm m-0 mb-6 leading-relaxed">سيتم حذف هذا الإبداع من حائط إنجازاتك. هل أنت متأكدة؟</p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button onClick={() => setDeleteConfirm(null)} className="w-full px-5 py-3 rounded-xl border-2 border-slate-200 bg-white cursor-pointer font-bold text-slate-700 hover:bg-slate-50 transition-all">إلغاء</button>
                <button onClick={() => handleDelete(deleteConfirm.id)} className="w-full px-5 py-3 rounded-xl bg-red-500 text-white font-bold border-none cursor-pointer shadow-md hover:bg-red-600 transition-all">تأكيد الحذف</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <SettingsModal 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
      />
    </div>
  )
}
