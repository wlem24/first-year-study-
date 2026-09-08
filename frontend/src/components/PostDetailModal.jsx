import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import confetti from 'canvas-confetti'
import { getPost } from '../services/api'

export default function PostDetailModal({ postId, onClose }) {
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentImg, setCurrentImg] = useState(0)

  useEffect(() => {
    getPost(postId)
      .then((data) => {
        setPost(data)
        if (data?.star_rating === 5) {
          confetti({
            particleCount: 75,
            spread: 60,
            origin: { y: 0.6 },
            colors: ['#fbbf24', '#f472b6', '#38bdf8', '#34d399', '#c084fc'],
          })
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [postId])

  const images = post?.images || []
  const files = post?.files || []

  const nextImg = useCallback(() => {
    if (images.length > 0) setCurrentImg((i) => (i + 1) % images.length)
  }, [images.length])

  const prevImg = useCallback(() => {
    if (images.length > 0) setCurrentImg((i) => (i - 1 + images.length) % images.length)
  }, [images.length])

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft') nextImg() // RTL flipped mapping
      if (e.key === 'ArrowRight') prevImg()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose, nextImg, prevImg])

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-[1000] flex items-center justify-center p-5 bg-slate-900/65 backdrop-blur-md"
      dir="rtl"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-white rounded-[28px] w-full max-w-[780px] max-h-[90vh] overflow-y-auto relative shadow-2xl"
      >
        <button
          onClick={onClose}
          className="absolute top-4 left-4 z-10 w-10 h-10 rounded-full bg-white/95 border-2 border-slate-200 text-slate-500 text-xl cursor-pointer flex items-center justify-center hover:bg-slate-50 transition-all"
        >
          ✕
        </button>

        {loading ? (
          <div className="p-16 text-center text-slate-400">
            <div className="skeleton h-[300px] rounded-2xl mb-5" />
            <div className="skeleton h-10 w-3/5 rounded-xl mx-auto" />
          </div>
        ) : post ? (
          <div>
            {images.length > 0 && (
              <div className="relative bg-slate-50 rounded-t-[28px] overflow-hidden">
                <AnimatePresence mode="wait">
                  <motion.img
                    key={currentImg}
                    src={images[currentImg].url}
                    alt=""
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-full max-h-[420px] object-contain block bg-slate-900"
                  />
                </AnimatePresence>

                {images.length > 1 && (
                  <>
                    <button onClick={nextImg} className="absolute top-1/2 left-3 -translate-y-1/2 w-9 h-9 rounded-full bg-black/55 text-white flex items-center justify-center text-2xl border-none cursor-pointer">‹</button>
                    <button onClick={prevImg} className="absolute top-1/2 right-3 -translate-y-1/2 w-9 h-9 rounded-full bg-black/55 text-white flex items-center justify-center text-2xl border-none cursor-pointer">›</button>
                    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                      {images.map((_, i) => (
                        <div
                          key={i}
                          onClick={() => setCurrentImg(i)}
                          className={`w-2 h-2 rounded-full cursor-pointer ${i === currentImg ? 'bg-white' : 'bg-white/40'}`}
                        />
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            <div className="p-7 md:p-8 flex flex-col gap-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="bg-purple-50 text-purple-600 px-3 py-1 rounded-full text-xs font-bold uppercase">
                  {post.subject || post.category}
                </span>
                <div className="text-xl" title={`${post.star_rating} نجوم!`}>
                  {'⭐'.repeat(post.star_rating || 5)}
                </div>
              </div>

              <h2 className="m-0 text-2xl font-extrabold text-text-dark">{post.title}</h2>

              {post.description && (
                <p className="m-0 text-slate-600 text-sm leading-relaxed whitespace-pre-wrap">
                  {post.description}
                </p>
              )}

              {post.audio_url && (
                <div className="bg-sky-50 border-2 border-sky-400 rounded-2xl p-4 flex items-center gap-3">
                  <span className="text-3xl">🎙️</span>
                  <div className="flex-1">
                    <div className="font-bold text-sm text-sky-700 mb-1">تسجيل صوتي / قراءة</div>
                    <audio controls src={post.audio_url} className="w-full h-9" />
                  </div>
                </div>
              )}

              {post.teacher_note && (
                <div className="bg-yellow-50 rounded-2xl p-4 shadow-sm border-2 border-dashed border-yellow-400">
                  <div className="font-bold text-xs text-amber-800 mb-1">🌟 ملاحظة المعلمة / الأم:</div>
                  <p className="m-0 font-bold text-amber-900 leading-snug">«{post.teacher_note}»</p>
                </div>
              )}

              {files.length > 0 && (
                <div>
                  <h4 className="m-0 mb-3 text-sm font-bold text-text-dark">
                    📎 أوراق العمل والملفات المرفقة ({files.length})
                  </h4>
                  <div className="flex flex-col gap-2">
                    {files.map((file) => (
                      <a
                        key={file.id}
                        href={file.url}
                        download={file.original_name}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border-2 border-slate-200 no-underline text-slate-800 transition-all hover:bg-slate-100"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">📄</span>
                          <div>
                            <div className="text-sm font-bold">{file.original_name}</div>
                            <div className="text-xs text-slate-400" dir="ltr">{formatSize(file.size_bytes)}</div>
                          </div>
                        </div>
                        <span className="text-xs font-bold text-purple-500">تحميل ↓</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-10 text-center font-bold text-slate-600">لم يتم العثور على النشاط.</div>
        )}
      </motion.div>
    </div>
  )
}
