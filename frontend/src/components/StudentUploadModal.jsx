import { motion, AnimatePresence } from 'framer-motion'

export default function StudentUploadModal({ isOpen, onClose, children }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 z-[1000] flex items-center justify-center bg-slate-900/65 backdrop-blur-md p-5"
          dir="rtl"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-[28px] p-6 md:p-8 w-full max-w-[640px] max-h-[88vh] overflow-y-auto shadow-2xl"
          >
            <div className="flex justify-end mb-2">
              <button
                onClick={onClose}
                className="bg-slate-100 border-none text-slate-500 text-xl cursor-pointer w-9 h-9 rounded-full flex items-center justify-center hover:bg-slate-200 transition-all"
              >
                ✕
              </button>
            </div>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
