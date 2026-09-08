import { motion } from 'framer-motion'

const SUBJECTS = [
  { id: 'all', label: 'جميع الإبداعات', icon: '🌈', color: '#f3e8ff', border: '#d8b4fe', text: '#6b21a8' },
  { id: 'art', label: 'رسوماتي وإبداعاتي', icon: '🎨', color: '#fce7f3', border: '#f472b6', text: '#9d174d' },
  { id: 'reading', label: 'قراءاتي وتسجيلاتي', icon: '📖', color: '#e0f2fe', border: '#38bdf8', text: '#0369a1' },
  { id: 'math', label: 'مرح الرياضيات', icon: '🔢', color: '#fef08a', border: '#facc15', text: '#854d0e' },
  { id: 'science', label: 'اكتشافات العلوم', icon: '🔬', color: '#dcfce7', border: '#4ade80', text: '#15803d' },
  { id: 'badges', label: 'أوسمتي وإنجازاتي', icon: '⭐', color: '#ffedd5', border: '#fb923c', text: '#9a3412' },
]

export default function SubjectFilter({ activeCategory, onSelectCategory }) {
  return (
    <div className="flex items-center gap-3 overflow-x-auto pb-3 px-1" style={{ scrollbarWidth: 'none' }}>
      {SUBJECTS.map((cat) => {
        const isActive = (activeCategory || 'all') === cat.id
        return (
          <motion.button
            key={cat.id}
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onSelectCategory(cat.id)}
            className="inline-flex items-center gap-2 px-5 py-2 rounded-full font-bold text-sm cursor-pointer whitespace-nowrap transition-all duration-200"
            style={{
              border: `2px solid ${isActive ? cat.border : '#e2e8f0'}`,
              background: isActive ? cat.color : '#ffffff',
              color: isActive ? cat.text : '#475569',
              boxShadow: isActive ? `0 4px 14px ${cat.border}40` : '0 2px 6px rgba(0, 0, 0, 0.04)',
              fontFamily: 'var(--font-cairo)',
            }}
          >
            <span className="text-lg">{cat.icon}</span>
            <span>{cat.label}</span>
          </motion.button>
        )
      })}
    </div>
  )
}
