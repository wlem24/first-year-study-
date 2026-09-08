import { useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { createPost, updatePost, getPost } from '../services/api'

const CATEGORY_OPTIONS = [
  { id: 'art', label: '🎨 رسوماتي وإبداعاتي' },
  { id: 'reading', label: '📖 قراءاتي وتسجيلاتي' },
  { id: 'math', label: '🔢 مرح الرياضيات' },
  { id: 'science', label: '🔬 اكتشافات العلوم' },
  { id: 'badges', label: '⭐ أوسمتي وإنجازاتي' },
  { id: 'activities', label: '🎈 أنشطة أخرى' },
]

const QUICK_CHEERS = [
  '🌟 خط جميل وعمل مرتب!',
  '📚 قراءة رائعة ومعبرة!',
  '🎨 ألوان مبدعة وجميلة!',
  '🔢 حل ممتاز لمسائل الرياضيات!',
  '⭐ نجمة الصف الأول اليوم!',
]

export default function UploadForm({ post, onSaved }) {
  const isEdit = !!post
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('art')
  const [subject, setSubject] = useState('')
  const [starRating, setStarRating] = useState(5)
  const [teacherNote, setTeacherNote] = useState('')
  const [audioFile, setAudioFile] = useState(null)
  const [newImages, setNewImages] = useState([])
  const [newFiles, setNewFiles] = useState([])
  const [existingImages, setExistingImages] = useState([])
  const [existingFiles, setExistingFiles] = useState([])
  const [removedImageIds, setRemovedImageIds] = useState([])
  const [removedFileIds, setRemovedFileIds] = useState([])
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (isEdit) {
      setTitle(post.title || '')
      setDescription(post.description || '')
      setCategory(post.category || 'art')
      setSubject(post.subject || '')
      setStarRating(post.star_rating || 5)
      setTeacherNote(post.teacher_note || '')
      getPost(post.id)
        .then((full) => {
          setExistingImages(full.images || [])
          setExistingFiles(full.files || [])
        })
        .catch(() => {})
    } else {
      setTitle('')
      setDescription('')
      setCategory('art')
      setSubject('')
      setStarRating(5)
      setTeacherNote('')
      setAudioFile(null)
      setNewImages([])
      setNewFiles([])
      setExistingImages([])
      setExistingFiles([])
      setRemovedImageIds([])
      setRemovedFileIds([])
    }
  }, [post, isEdit])

  const imageDropzone = useDropzone({
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [], 'image/gif': [] },
    onDrop: (accepted) => setNewImages((prev) => [...prev, ...accepted]),
  })

  const fileDropzone = useDropzone({
    accept: {
      'application/pdf': [],
      'application/zip': [],
      'application/msword': [],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [],
      'audio/mpeg': [],
      'audio/wav': [],
    },
    onDrop: (accepted) => setNewFiles((prev) => [...prev, ...accepted]),
  })

  const toggleRemoveImage = (id) => {
    setRemovedImageIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const toggleRemoveFile = (id) => {
    setRemovedFileIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) {
      toast.error('الرجاء إدخال عنوان للنشاط!')
      return
    }

    setSubmitting(true)
    const formData = new FormData()
    formData.append('title', title)
    formData.append('description', description)
    formData.append('category', category)
    formData.append('subject', subject || title)
    formData.append('star_rating', starRating)
    formData.append('teacher_note', teacherNote)

    if (audioFile) {
      formData.append('audio', audioFile)
    }

    newImages.forEach((img) => formData.append('images', img))
    newFiles.forEach((f) => formData.append('files', f))

    if (isEdit) {
      if (removedImageIds.length > 0) formData.append('remove_image_ids', removedImageIds.join(','))
      if (removedFileIds.length > 0) formData.append('remove_file_ids', removedFileIds.join(','))
    }

    try {
      if (isEdit) {
        await updatePost(post.id, formData)
        toast.success('تم تحديث النشاط على الحائط! ⭐')
      } else {
        await createPost(formData)
        toast.success('تم تثبيت الإبداع على الحائط! 🎉')
      }
      onSaved?.()
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'حدث خطأ أثناء حفظ النشاط')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" dir="rtl">
      <div>
        <h2 className="m-0 text-xl font-extrabold text-text-dark">
          {isEdit ? '✏️ تعديل النشاط' : '📌 تثبيت إبداع جديد'}
        </h2>
        <p className="m-0 mt-1 text-sm text-slate-500">
          ارفعي الرسومات، تسجيلات القراءة، أوراق العمل، وامنحي النجوم!
        </p>
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">القسم / نوع النشاط *</label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {CATEGORY_OPTIONS.map((c) => (
            <button
              type="button"
              key={c.id}
              onClick={() => setCategory(c.id)}
              className={`px-3 py-2 rounded-xl border-2 font-bold text-xs cursor-pointer text-right transition-all ${
                category === c.id ? 'border-purple-500 bg-purple-50 text-purple-700' : 'border-slate-200 bg-white text-slate-600'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">العنوان *</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="مثال: لوحتي بألوان الباستيل المائية"
          required
          className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500"
          style={{ fontFamily: 'var(--font-cairo)' }}
        />
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">تقييم النجوم</label>
        <div className="flex items-center gap-1.5">
          {[1, 2, 3, 4, 5].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStarRating(s)}
              className={`bg-transparent border-none text-3xl cursor-pointer transition-all ${
                s <= starRating ? 'scale-110 opacity-100' : 'scale-95 opacity-30'
              }`}
            >
              ⭐
            </button>
          ))}
          <span className="mr-2 text-sm font-bold text-yellow-600">{starRating} نجوم!</span>
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">ملاحظة تشجيعية (تظهر في فقاعة)</label>
        <input
          value={teacherNote}
          onChange={(e) => setTeacherNote(e.target.value)}
          placeholder="مثال: رسمة رائعة جداً وألوان مذهلة!"
          className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500 mb-2"
          style={{ fontFamily: 'var(--font-cairo)' }}
        />
        <div className="flex flex-wrap gap-1.5">
          {QUICK_CHEERS.map((q, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setTeacherNote(q)}
              className="bg-yellow-50 border border-yellow-400 rounded-full px-3 py-1 text-xs text-amber-800 cursor-pointer hover:bg-yellow-100"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">الوصف / القصة</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="ماذا تعلمت أو فعلت ميان في هذا النشاط؟"
          rows={3}
          className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 text-sm outline-none focus:border-purple-500 resize-y"
          style={{ fontFamily: 'var(--font-cairo)' }}
        />
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">🎙️ تسجيل صوتي (MP3/WAV/M4A)</label>
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
          className="w-full px-4 py-2 rounded-xl border-2 border-slate-200 text-sm"
        />
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">📸 صور ورسومات (JPG, PNG, WebP)</label>
        <div
          {...imageDropzone.getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-all ${
            imageDropzone.isDragActive ? 'border-purple-500 bg-purple-50' : 'border-slate-300 bg-slate-50'
          }`}
        >
          <input {...imageDropzone.getInputProps()} />
          <p className="m-0 text-sm font-bold text-slate-500">
            {imageDropzone.isDragActive ? '🎨 أفلتي الصور هنا!' : '🎨 اسحبي وأفلتي الصور، أو اضغطي للاختيار'}
          </p>
        </div>

        {isEdit && existingImages.length > 0 && (
          <div className="flex gap-2 flex-wrap mt-2">
            {existingImages.map((img) => (
              <div
                key={img.id}
                onClick={() => toggleRemoveImage(img.id)}
                className={`w-14 h-14 rounded-xl overflow-hidden cursor-pointer relative border-2 ${
                  removedImageIds.includes(img.id) ? 'border-red-500 opacity-40' : 'border-slate-200'
                }`}
              >
                <img src={img.url} alt="" className="w-full h-full object-cover" />
                {removedImageIds.includes(img.id) && (
                  <span className="absolute inset-0 flex items-center justify-center text-red-500 font-bold">✕</span>
                )}
              </div>
            ))}
          </div>
        )}

        {newImages.length > 0 && (
          <div className="flex gap-1.5 flex-wrap mt-2">
            {newImages.map((f, i) => (
              <span key={i} className="px-2 py-1 rounded bg-pink-100 text-pink-700 text-xs">
                {f.name}
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1">📄 أوراق عمل وملفات PDF (اختياري)</label>
        <div
          {...fileDropzone.getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-all ${
            fileDropzone.isDragActive ? 'border-purple-500 bg-purple-50' : 'border-slate-300 bg-slate-50'
          }`}
        >
          <input {...fileDropzone.getInputProps()} />
          <p className="m-0 text-sm font-bold text-slate-500">
            {fileDropzone.isDragActive ? '📄 أفلتي الملفات هنا!' : '📄 اسحبي وأفلتي الملفات، أو اضغطي للاختيار'}
          </p>
        </div>
        {newFiles.length > 0 && (
          <div className="flex gap-1.5 flex-wrap mt-2">
            {newFiles.map((f, i) => (
              <span key={i} className="px-2 py-1 rounded bg-sky-100 text-sky-700 text-xs">
                {f.name}
              </span>
            ))}
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="w-full py-3.5 mt-2 rounded-xl bg-gradient-to-l from-purple-500 to-pink-500 text-white font-bold text-base border-none cursor-pointer shadow-md disabled:opacity-70 transition-all hover:-translate-y-0.5 hover:shadow-lg"
      >
        {submitting ? 'جاري الحفظ...' : isEdit ? 'تحديث النشاط' : '🌟 تثبيت على الحائط!'}
      </button>
    </form>
  )
}
