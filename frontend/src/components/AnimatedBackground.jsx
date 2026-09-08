import { useState, useEffect, useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

/**
 * AnimatedBackground — خلفية تفاعلية مبهجة للصف الأول:
 * - فراشات ملونة عائمة
 * - غيوم ناعمة متحركة
 * - نجوم متلألئة
 * - شخصية أولي البومة العالمة (أسفل اليسار)
 * - شخصية بيب الأرنبة النجمة (أسفل اليمين)
 */
export default function AnimatedBackground() {
  const prefersReduced = useReducedMotion()
  const [dims, setDims] = useState({ w: window.innerWidth, h: window.innerHeight })

  useEffect(() => {
    const handleResize = () => setDims({ w: window.innerWidth, h: window.innerHeight })
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const butterflies = useMemo(
    () =>
      Array.from({ length: 6 }, (_, i) => ({
        id: i,
        color: ['#c084fc', '#f472b6', '#38bdf8', '#fbbf24', '#34d399', '#f43f5e'][i],
        size: 24 + (i % 3) * 6,
        startX: 10 + i * 16,
        startY: 20 + (i % 4) * 20,
        duration: 20 + (i % 3) * 6,
        delay: i * 2.5,
      })),
    []
  )

  const clouds = useMemo(
    () => [
      { id: 1, y: 40, scale: 0.9, duration: 45, delay: 0 },
      { id: 2, y: 120, scale: 0.7, duration: 55, delay: 15 },
      { id: 3, y: 80, scale: 1.1, duration: 40, delay: 28 },
    ],
    []
  )

  if (prefersReduced) return null

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      {clouds.map((c) => (
        <DriftingCloud key={c.id} {...c} dims={dims} />
      ))}
      <TwinklingStars />
      {butterflies.map((b) => (
        <Butterfly key={b.id} {...b} dims={dims} />
      ))}
      {/* Mascots with absolute anchors inside fixed corners */}
      <div className="fixed bottom-4 right-4 z-10 pointer-events-auto">
        <OllieTheOwl />
      </div>
      <div className="fixed bottom-4 left-4 z-10 pointer-events-auto">
        <PipTheStarBuddy />
      </div>
    </div>
  )
}

function Butterfly({ color, size, startX, startY, duration, delay, dims }) {
  const x1 = (startX / 100) * dims.w
  const y1 = (startY / 100) * dims.h
  const x2 = x1 + 140
  const y2 = y1 - 80
  const x3 = x1 - 100
  const y3 = y1 + 70

  return (
    <motion.div
      initial={{ x: x1, y: y1, opacity: 0 }}
      animate={{
        x: [x1, x2, x3, x1],
        y: [y1, y2, y3, y1],
        opacity: [0, 0.75, 0.85, 0],
        rotate: [0, 15, -12, 0],
      }}
      transition={{ duration, delay, repeat: Infinity, ease: 'easeInOut' }}
      style={{ position: 'absolute', width: size, height: size }}
    >
      <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: '100%', height: '100%' }}>
        <motion.ellipse cx="15" cy="16" rx="12" ry="14" fill={color} fillOpacity={0.75} animate={{ rx: [12, 3, 12] }} transition={{ duration: 0.35, repeat: Infinity, ease: 'easeInOut' }} />
        <motion.ellipse cx="14" cy="27" rx="8" ry="10" fill={color} fillOpacity={0.55} animate={{ rx: [8, 2, 8] }} transition={{ duration: 0.35, repeat: Infinity, ease: 'easeInOut' }} />
        <motion.ellipse cx="25" cy="16" rx="12" ry="14" fill={color} fillOpacity={0.75} animate={{ rx: [12, 3, 12] }} transition={{ duration: 0.35, repeat: Infinity, ease: 'easeInOut', delay: 0.05 }} />
        <motion.ellipse cx="26" cy="27" rx="8" ry="10" fill={color} fillOpacity={0.55} animate={{ rx: [8, 2, 8] }} transition={{ duration: 0.35, repeat: Infinity, ease: 'easeInOut', delay: 0.05 }} />
        <ellipse cx="20" cy="22" rx="2" ry="10" fill="#334155" />
        <circle cx="15" cy="6" r="1.5" fill={color} />
        <circle cx="25" cy="6" r="1.5" fill={color} />
        <line x1="19" y1="13" x2="15" y2="6" stroke="#334155" strokeWidth="1" strokeLinecap="round" />
        <line x1="21" y1="13" x2="25" y2="6" stroke="#334155" strokeWidth="1" strokeLinecap="round" />
      </svg>
    </motion.div>
  )
}

function DriftingCloud({ y, scale, duration, delay, dims }) {
  return (
    <motion.div
      initial={{ x: dims.w + 200, y }}
      animate={{ x: -200 }}
      transition={{ duration, delay, repeat: Infinity, ease: 'linear' }}
      style={{ position: 'absolute', transform: `scale(${scale})`, opacity: 0.35 }}
    >
      <svg width="180" height="70" viewBox="0 0 180 70" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M30 50 Q10 50 10 35 Q10 20 28 22 Q35 8 55 10 Q70 12 75 25 Q88 15 105 20 Q120 24 120 38 Q135 38 135 50 Z" fill="#e2e8f0" />
      </svg>
    </motion.div>
  )
}

function TwinklingStars() {
  const stars = [
    { top: '15%', left: '20%', delay: 0 },
    { top: '25%', left: '85%', delay: 1.2 },
    { top: '65%', left: '12%', delay: 0.6 },
    { top: '75%', left: '78%', delay: 1.8 },
    { top: '45%', left: '92%', delay: 2.4 },
  ]
  return (
    <>
      {stars.map((s, idx) => (
        <motion.div
          key={idx}
          animate={{ scale: [0.6, 1.2, 0.6], opacity: [0.3, 0.9, 0.3], rotate: [0, 45, 0] }}
          transition={{ duration: 3, delay: s.delay, repeat: Infinity, ease: 'easeInOut' }}
          style={{ position: 'absolute', top: s.top, left: s.left }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="#fbbf24">
            <path d="M12 2L14.4 8.6L21.5 9.2L16.2 13.8L17.8 20.8L12 17.2L6.2 20.8L7.8 13.8L2.5 9.2L9.6 8.6L12 2Z" />
          </svg>
        </motion.div>
      ))}
    </>
  )
}

function OllieTheOwl() {
  const [clicked, setClicked] = useState(false)
  const [message, setMessage] = useState('هيّا للتعلّم! ✨')

  const handleClick = () => {
    setClicked(true)
    const cheers = [
      'أنتِ رائعة! 🌟',
      'رسمة جميلة اليوم! 🎨',
      'برافو على القراءة! 📖',
      'نجمة الصف الأول! ⭐',
      'استمري في التألق! 🌈',
    ]
    setMessage(cheers[Math.floor(Math.random() * cheers.length)])
    setTimeout(() => setClicked(false), 2400)
  }

  return (
    <motion.div
      whileHover={{ scale: 1.1, y: -6 }}
      whileTap={{ scale: 0.95 }}
      onClick={handleClick}
      style={{ cursor: 'pointer', position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
    >
      {clicked && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.8 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: 'absolute', bottom: '100%', marginBottom: '8px',
            background: '#ffffff', border: '2px solid #38bdf8', borderRadius: '16px',
            padding: '6px 14px', fontSize: '0.85rem', fontWeight: 700, color: '#0284c7',
            whiteSpace: 'nowrap', boxShadow: '0 8px 16px rgba(56, 189, 248, 0.25)', zIndex: 30,
            fontFamily: 'var(--font-cairo)',
          }}
        >
          {message}
        </motion.div>
      )}
      <svg width="88" height="98" viewBox="0 0 88 98" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M44 8 L68 18 L44 28 L20 18 Z" fill="#3b82f6" />
        <rect x="36" y="24" width="16" height="8" rx="2" fill="#1d4ed8" />
        <path d="M58 22 Q64 28 66 36" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round" />
        <circle cx="66" cy="37" r="2.5" fill="#f59e0b" />
        <path d="M26 34 L18 20 L34 28 Z" fill="#38bdf8" />
        <path d="M62 34 L70 20 L54 28 Z" fill="#38bdf8" />
        <ellipse cx="44" cy="58" rx="30" ry="32" fill="#38bdf8" />
        <ellipse cx="44" cy="64" rx="20" ry="22" fill="#e0f2fe" />
        <path d="M38 56 Q44 60 50 56" stroke="#7dd3fc" strokeWidth="2" strokeLinecap="round" />
        <path d="M36 64 Q44 68 52 64" stroke="#7dd3fc" strokeWidth="2" strokeLinecap="round" />
        <path d="M38 72 Q44 76 50 72" stroke="#7dd3fc" strokeWidth="2" strokeLinecap="round" />
        <circle cx="32" cy="46" r="11" fill="#ffffff" stroke="#bae6fd" strokeWidth="2" />
        <circle cx="56" cy="46" r="11" fill="#ffffff" stroke="#bae6fd" strokeWidth="2" />
        <circle cx="34" cy="46" r="6" fill="#0f172a" />
        <circle cx="54" cy="46" r="6" fill="#0f172a" />
        <circle cx="32" cy="43" r="2.5" fill="#ffffff" />
        <circle cx="52" cy="43" r="2.5" fill="#ffffff" />
        <circle cx="36" cy="48" r="1" fill="#ffffff" />
        <circle cx="56" cy="48" r="1" fill="#ffffff" />
        <path d="M40 52 L48 52 L44 60 Z" fill="#f59e0b" />
        <circle cx="23" cy="54" r="4" fill="#f472b6" fillOpacity="0.45" />
        <circle cx="65" cy="54" r="4" fill="#f472b6" fillOpacity="0.45" />
        <ellipse cx="34" cy="88" rx="6" ry="3.5" fill="#f59e0b" />
        <ellipse cx="54" cy="88" rx="6" ry="3.5" fill="#f59e0b" />
      </svg>
    </motion.div>
  )
}

function PipTheStarBuddy() {
  const [clicked, setClicked] = useState(false)
  const [message, setMessage] = useState('يااي! طالبة نجمة! ⭐')

  const handleClick = () => {
    setClicked(true)
    const cheers = [
      '5 نجوم ذهبية لكِ! ⭐⭐⭐⭐⭐',
      'أنتِ مذهلة! 💖',
      'أفضل عمل مدرسي! 📝',
      'هاي فايف! 🖐️',
      'فخورة بكِ جداً! 🎈',
    ]
    setMessage(cheers[Math.floor(Math.random() * cheers.length)])
    setTimeout(() => setClicked(false), 2400)
  }

  return (
    <motion.div
      whileHover={{ scale: 1.1, y: -6 }}
      whileTap={{ scale: 0.95 }}
      onClick={handleClick}
      style={{ cursor: 'pointer', position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
    >
      {clicked && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.8 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: 'absolute', bottom: '100%', marginBottom: '8px',
            background: '#ffffff', border: '2px solid #f472b6', borderRadius: '16px',
            padding: '6px 14px', fontSize: '0.85rem', fontWeight: 700, color: '#db2777',
            whiteSpace: 'nowrap', boxShadow: '0 8px 16px rgba(244, 114, 182, 0.25)', zIndex: 30,
            fontFamily: 'var(--font-cairo)',
          }}
        >
          {message}
        </motion.div>
      )}
      <svg width="84" height="98" viewBox="0 0 84 98" fill="none" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="28" cy="22" rx="9" ry="20" fill="#f472b6" transform="rotate(-12 28 22)" />
        <ellipse cx="28" cy="22" rx="5.5" ry="14" fill="#fce7f3" transform="rotate(-12 28 22)" />
        <ellipse cx="56" cy="22" rx="9" ry="20" fill="#f472b6" transform="rotate(12 56 22)" />
        <ellipse cx="56" cy="22" rx="5.5" ry="14" fill="#fce7f3" transform="rotate(12 56 22)" />
        <circle cx="42" cy="52" r="26" fill="#f472b6" />
        <ellipse cx="42" cy="56" rx="16" ry="14" fill="#fce7f3" />
        <path d="M24 36 L26 40 L30 40 L27 42 L28 46 L24 43 L20 46 L21 42 L18 40 L22 40 Z" fill="#fbbf24" />
        <ellipse cx="34" cy="48" rx="4" ry="5.5" fill="#1e293b" />
        <ellipse cx="50" cy="48" rx="4" ry="5.5" fill="#1e293b" />
        <circle cx="32.5" cy="46" r="2" fill="#ffffff" />
        <circle cx="48.5" cy="46" r="2" fill="#ffffff" />
        <circle cx="42" cy="54" r="2" fill="#db2777" />
        <path d="M37 57 Q40 60 42 58 Q44 60 47 57" stroke="#1e293b" strokeWidth="1.6" fill="none" strokeLinecap="round" />
        <circle cx="26" cy="56" r="4.5" fill="#fb7185" fillOpacity="0.5" />
        <circle cx="58" cy="56" r="4.5" fill="#fb7185" fillOpacity="0.5" />
        <ellipse cx="42" cy="80" rx="20" ry="14" fill="#f472b6" />
        <ellipse cx="42" cy="82" rx="12" ry="8" fill="#fce7f3" />
        <circle cx="28" cy="74" r="5" fill="#fce7f3" stroke="#f472b6" strokeWidth="2" />
        <circle cx="56" cy="74" r="5" fill="#fce7f3" stroke="#f472b6" strokeWidth="2" />
        <line x1="56" y1="74" x2="68" y2="52" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M68 46 L70 50 L74 50 L71 52 L72 56 L68 53 L64 56 L65 52 L62 50 L66 50 Z" fill="#fbbf24" />
        <ellipse cx="32" cy="90" rx="7" ry="4" fill="#f472b6" />
        <ellipse cx="52" cy="90" rx="7" ry="4" fill="#f472b6" />
      </svg>
    </motion.div>
  )
}
