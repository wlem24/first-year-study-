import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getPosts } from '../services/api'
import Navbar from '../components/Navbar'
import SubjectFilter from '../components/SubjectFilter'
import StudentPostCard from '../components/StudentPostCard'
import PostDetailModal from '../components/PostDetailModal'

export default function Home() {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeCategory, setActiveCategory] = useState('all')
  const [search, setSearch] = useState('')
  const [selectedPostId, setSelectedPostId] = useState(null)

  const fetchPosts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getPosts({
        category: activeCategory,
        search,
        page: 1,
        pageSize: 60,
      })
      setPosts(data.items || [])
    } catch {
      setPosts([])
    } finally {
      setLoading(false)
    }
  }, [activeCategory, search])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPosts()
    }, 200)
    return () => clearTimeout(timer)
  }, [fetchPosts])

  return (
    <>
      <Navbar search={search} onSearchChange={setSearch} />

      <main className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24">
        {/* بانر الترحيب */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="bg-gradient-to-l from-pastel-yellow via-pastel-pink to-pastel-blue rounded-3xl p-6 md:px-8 mb-8 border-2 border-white/80 shadow-lg flex flex-col lg:flex-row items-center justify-between gap-6 text-center lg:text-right w-full"
        >
          <div className="flex-1">
            <div className="flex flex-col sm:flex-row items-center gap-3 mb-2 justify-center lg:justify-start">
              <span className="text-4xl hidden sm:inline-block">🌟</span>
              <h2 className="m-0 text-xl md:text-2xl font-extrabold text-text-dark">
                مرحباً بكم في رحلتي في الصف الأول الابتدائي! 🌟
              </h2>
            </div>
            <p className="m-0 text-sm sm:text-base text-slate-700 max-w-2xl mx-auto lg:mx-0 font-medium leading-relaxed">
              شاهدوا رسوماتي 🎨، استمعوا لتسجيلات قراءتي 🎙️، تفقدوا صواريخ الرياضيات 🚀، وشاهدوا أوسمتي! ⭐
            </p>
          </div>
          <div className="bg-white/95 backdrop-blur-sm px-6 py-3 rounded-full text-sm font-bold text-primary shadow-sm flex items-center justify-center gap-2 whitespace-nowrap border border-white/50 w-full sm:w-auto">
            <span className="text-lg">📌</span>
            <span>{posts.length} إبداع مثبّت</span>
          </div>
        </motion.div>

        {/* تبويبات المواد */}
        <div className="mb-8 w-full overflow-hidden max-w-[100vw]">
          <SubjectFilter activeCategory={activeCategory} onSelectCategory={setActiveCategory} />
        </div>

        {/* الشبكة */}
        <div className="flex-1 w-full relative">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 sm:gap-8">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="skeleton h-[380px] rounded-3xl w-full" />
              ))}
            </div>
          ) : posts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center justify-center p-8 sm:p-16 text-center border-2 border-dashed border-slate-300 rounded-3xl gap-4 bg-white/80 my-8 w-full max-w-3xl mx-auto"
            >
              <div className="text-6xl mb-2">{search ? '🔍' : '🎨'}</div>
              <h3 className="m-0 mb-1 text-xl sm:text-2xl text-text-dark font-extrabold">
                {search ? 'لا توجد إبداعات تطابق بحثك!' : 'لا توجد إبداعات في هذا القسم بعد!'}
              </h3>
              <p className="m-0 text-text-muted text-sm sm:text-base leading-relaxed">
                {search ? 'جربي البحث عن رسم أو قراءة أو رياضيات.' : 'عودي قريباً لرؤية أعمال ميان الجديدة!'}
              </p>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 sm:gap-8 justify-items-center w-full">
              {posts.map((post, idx) => (
                <div key={post.id} className="w-full max-w-[360px]">
                  <StudentPostCard
                    post={post}
                    index={idx}
                    onClick={(p) => setSelectedPostId(p.id)}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <AnimatePresence>
        {selectedPostId && (
          <PostDetailModal
            postId={selectedPostId}
            onClose={() => setSelectedPostId(null)}
          />
        )}
      </AnimatePresence>
    </>
  )
}
