import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function Navbar({ search, onSearchChange }) {
  return (
    <motion.header
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="sticky top-0 z-[100] w-full bg-white/90 backdrop-blur-xl border-b-2 border-slate-200/80 shadow-sm"
    >
      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 py-4">
        {/* الشعار والعنوان */}
        <Link to="/" className="flex items-center gap-3 no-underline w-full md:w-auto justify-center md:justify-start">
          <div className="w-12 h-12 flex-shrink-0 rounded-2xl bg-gradient-to-br from-pastel-yellow to-pastel-pink flex items-center justify-center text-2xl shadow-md">
            🎒
          </div>
          <div className="flex flex-col items-center md:items-start text-center md:text-right">
            <div className="flex items-center gap-2 flex-wrap justify-center md:justify-start">
              <h1 className="text-lg md:text-xl font-extrabold text-text-dark m-0 tracking-tight">
                حائط إنجازات ميان
              </h1>
              <span className="bg-pastel-yellow text-amber-800 text-[10px] sm:text-xs font-bold px-2 py-0.5 rounded-full border border-yellow-300 whitespace-nowrap">
                الصف الأول ⭐
              </span>
            </div>
            <p className="m-0 text-xs text-text-muted mt-0.5">
              رسوماتي • قراءاتي • رياضيات • إنجازاتي
            </p>
          </div>
        </Link>

        {/* البحث وأيقونة الدخول */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto justify-center md:justify-end">
          {onSearchChange !== undefined && (
            <div className="relative w-full sm:w-auto flex-1 sm:flex-none">
              <input
                type="text"
                placeholder="🔍 ابحثي عن نشاط..."
                value={search || ''}
                onChange={(e) => onSearchChange(e.target.value)}
                className="w-full sm:w-56 px-4 py-2 rounded-full border-2 border-slate-200 bg-white text-sm outline-none transition-all focus:border-purple-500"
                style={{ fontFamily: 'var(--font-cairo)' }}
              />
            </div>
          )}

          {/* أيقونة دخول سرية للمعلمة/الأم */}
          <Link
            to="/login"
            title="دخول المعلمة / الأم"
            className="w-10 h-10 flex-shrink-0 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center no-underline text-lg text-slate-400 hover:bg-pastel-yellow hover:text-amber-800 hover:border-yellow-300 transition-all"
          >
            🔒
          </Link>
        </div>
      </div>
    </motion.header>
  )
}
