import { useState } from 'react'
import { motion } from 'framer-motion'
import AudioPlayer from './AudioPlayer'

const CATEGORY_STYLES = {
  art: { bg: '#fce7f3', border: '#f472b6', text: '#9d174d', icon: '🎨', tapeClass: 'washi-tape-pink', badge: 'رسوماتي' },
  reading: { bg: '#e0f2fe', border: '#38bdf8', text: '#0369a1', icon: '📖', tapeClass: 'washi-tape-blue', badge: 'قراءاتي' },
  math: { bg: '#fef08a', border: '#facc15', text: '#854d0e', icon: '🔢', tapeClass: 'washi-tape', badge: 'رياضيات' },
  science: { bg: '#dcfce7', border: '#4ade80', text: '#15803d', icon: '🔬', tapeClass: 'washi-tape-green', badge: 'علوم' },
  badges: { bg: '#ffedd5', border: '#fb923c', text: '#9a3412', icon: '⭐', tapeClass: 'washi-tape', badge: 'أوسمتي' },
  activities: { bg: '#f3e8ff', border: '#c084fc', text: '#6b21a8', icon: '🎈', tapeClass: 'washi-tape', badge: 'أنشطة' },
}

export default function StudentPostCard({ post, index, onClick }) {
  const categoryStyle = CATEGORY_STYLES[post.category] || CATEGORY_STYLES.art
  const starsCount = post.star_rating || 5
  const rotation = ((index % 5) - 2) * 1.2

  // عداد الإعجابات
  const [likes, setLikes] = useState(post.likes || 0)
  const [hearting, setHearting] = useState(false)

  const handleLike = async (e) => {
    e.stopPropagation()
    if (hearting) return
    setHearting(true)
    setLikes((prev) => prev + 1)
    try {
      const { likePost } = await import('../services/api')
      await likePost(post.id)
    } catch {}
    setTimeout(() => setHearting(false), 1200)
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9, y: 30 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
      whileHover={{ scale: 1.035, rotate: 0, y: -6, zIndex: 10 }}
      onClick={() => onClick(post)}
      className="relative bg-white rounded-3xl p-4 shadow-lg border-2 border-slate-100 cursor-pointer flex flex-col transition-all duration-300"
      style={{ transform: `rotate(${rotation}deg)` }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = categoryStyle.border)}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = '#f1f5f9')}
    >
      <div className={`washi-tape ${categoryStyle.tapeClass}`} />

      {/* إطار الصورة */}
      <div
        className="relative w-full rounded-2xl overflow-hidden mt-1.5"
        style={{ paddingTop: '68%', background: categoryStyle.bg, boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.06)' }}
      >
        {post.thumbnail_url ? (
          <img
            src={post.thumbnail_url}
            alt={post.title}
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-5xl">
            {categoryStyle.icon}
          </div>
        )}

        {/* زر الإعجاب العائم */}
        <motion.button
          whileTap={{ scale: 1.4 }}
          onClick={handleLike}
          className="absolute bottom-2 left-2 bg-white/90 border-2 border-pink-300 rounded-full px-3 py-1 text-sm font-bold text-pink-500 cursor-pointer shadow-md flex items-center gap-1 z-10"
        >
          <motion.span
            animate={hearting ? { scale: [1, 1.5, 1], rotate: [0, -15, 15, 0] } : {}}
            transition={{ duration: 0.5 }}
          >
            ❤️
          </motion.span>
          <span>{likes}</span>
        </motion.button>
      </div>

      {/* تفاصيل المنشور */}
      <div className="pt-3 px-1 pb-1 flex flex-col gap-2 flex-1">
        <div className="flex items-center justify-between">
          <span
            className="px-3 py-0.5 rounded-full text-xs font-bold"
            style={{ background: categoryStyle.bg, color: categoryStyle.text, border: `1.5px solid ${categoryStyle.border}` }}
          >
            {categoryStyle.icon} {post.subject || categoryStyle.badge}
          </span>
          <div className="star-rating" title={`${starsCount} نجوم!`}>
            {'⭐'.repeat(starsCount)}
          </div>
        </div>

        <h3 className="m-0 text-base font-bold text-text-dark leading-snug">
          {post.title}
        </h3>

        {post.description && (
          <p className="m-0 text-sm text-text-muted leading-relaxed line-clamp-2">
            {post.description}
          </p>
        )}

        {/* مشغل الصوت */}
        {post.audio_url && (
          <div onClick={(e) => e.stopPropagation()}>
            <AudioPlayer src={post.audio_url} label="استمعي لي 🎙️" />
          </div>
        )}

        {post.teacher_note && (
          <div className="bg-yellow-50 border border-dashed border-yellow-400 rounded-xl px-3 py-1.5 text-xs text-amber-800 flex items-center gap-1.5">
            <span>💬</span>
            <span className="overflow-hidden text-ellipsis whitespace-nowrap">
              «{post.teacher_note}»
            </span>
          </div>
        )}

        <div className="mt-auto pt-1.5 text-xs text-text-light">
          ثُبّت بتاريخ {new Date(post.created_at).toLocaleDateString('ar-SA', { month: 'short', day: 'numeric', year: 'numeric' })}
        </div>
      </div>
    </motion.div>
  )
}
