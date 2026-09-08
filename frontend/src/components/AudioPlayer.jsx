import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

export default function AudioPlayer({ src, label = 'استمعي لي 🎙️' }) {
  const audioRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const onTimeUpdate = () => {
      if (audio.duration) setProgress((audio.currentTime / audio.duration) * 100)
    }
    const onLoadedMeta = () => setDuration(audio.duration)
    const onEnded = () => { setIsPlaying(false); setProgress(0) }

    audio.addEventListener('timeupdate', onTimeUpdate)
    audio.addEventListener('loadedmetadata', onLoadedMeta)
    audio.addEventListener('ended', onEnded)
    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate)
      audio.removeEventListener('loadedmetadata', onLoadedMeta)
      audio.removeEventListener('ended', onEnded)
    }
  }, [src])

  const togglePlay = (e) => {
    e?.stopPropagation?.()
    const audio = audioRef.current
    if (!audio) return
    if (isPlaying) {
      audio.pause()
    } else {
      audio.play()
    }
    setIsPlaying(!isPlaying)
  }

  const formatTime = (t) => {
    if (!t || isNaN(t)) return '0:00'
    const m = Math.floor(t / 60)
    const s = Math.floor(t % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const handleSeek = (e) => {
    e.stopPropagation()
    const audio = audioRef.current
    if (!audio || !audio.duration) return
    const rect = e.currentTarget.getBoundingClientRect()
    // RTL: calculate from right
    const clickX = rect.right - e.clientX
    const pct = clickX / rect.width
    audio.currentTime = pct * audio.duration
  }

  return (
    <div
      className="flex items-center gap-3 bg-sky-50 border-2 border-sky-200 rounded-2xl px-4 py-2 cursor-pointer"
      onClick={togglePlay}
    >
      <audio ref={audioRef} src={src} preload="metadata" />

      {/* زر التشغيل */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={togglePlay}
        className="w-10 h-10 rounded-full bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center text-white text-lg border-none cursor-pointer shadow-md flex-shrink-0"
      >
        {isPlaying ? '⏸️' : '▶️'}
      </motion.button>

      {/* شريط التقدم */}
      <div className="flex-1 flex flex-col gap-1 min-w-0">
        <div className="text-xs font-bold text-sky-700">{label}</div>
        <div
          className="h-3 bg-sky-100 rounded-full overflow-hidden cursor-pointer relative"
          onClick={handleSeek}
        >
          <motion.div
            className="h-full rounded-full bg-gradient-to-l from-sky-400 to-pink-400"
            style={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-sky-500 font-semibold">
          <span>{formatTime(audioRef.current?.currentTime || 0)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  )
}
