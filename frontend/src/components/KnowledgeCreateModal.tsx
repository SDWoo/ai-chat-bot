import React, { useState } from 'react'
import { X, Plus, Tag as TagIcon } from 'lucide-react'
import { knowledgeService, KnowledgeEntryCreate } from '../services/api'

interface KnowledgeCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function KnowledgeCreateModal({
  isOpen,
  onClose,
  onSuccess,
}: KnowledgeCreateModalProps) {
  const [formData, setFormData] = useState<KnowledgeEntryCreate>({
    title: '',
    content: '',
    category: null,
    tags: [],
    author: '',
    status: 'published',
  })
  const [tagInput, setTagInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // 유효성 검사
    if (!formData.title.trim()) {
      setError('제목을 입력해주세요.')
      return
    }
    if (!formData.content.trim()) {
      setError('내용을 입력해주세요.')
      return
    }

    try {
      setLoading(true)
      
      // 빈 값 제거
      const submitData: KnowledgeEntryCreate = {
        title: formData.title.trim(),
        content: formData.content.trim(),
        status: formData.status,
      }
      
      if (formData.category) {
        submitData.category = formData.category
      }
      if (formData.tags && formData.tags.length > 0) {
        submitData.tags = formData.tags
      }
      if (formData.author?.trim()) {
        submitData.author = formData.author.trim()
      }

      await knowledgeService.createKnowledgeEntry(submitData)
      
      // 성공 시 폼 초기화 및 모달 닫기
      setFormData({
        title: '',
        content: '',
        category: null,
        tags: [],
        author: '',
        status: 'published',
      })
      setTagInput('')
      onSuccess()
      onClose()
    } catch (err: any) {
      console.error('Failed to create knowledge entry:', err)
      setError(err.response?.data?.detail || '지식 항목 생성에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddTag = () => {
    const tag = tagInput.trim()
    if (tag && !formData.tags?.includes(tag)) {
      setFormData({
        ...formData,
        tags: [...(formData.tags || []), tag],
      })
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags?.filter(tag => tag !== tagToRemove) || [],
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAddTag()
    }
  }

  const categoryOptions = [
    { value: '', label: '선택하지 않음' },
    { value: 'error_fix', label: '에러 해결' },
    { value: 'tech_share', label: '기술 공유' },
    { value: 'how_to', label: '사용법' },
    { value: 'best_practice', label: '모범 사례' },
    { value: 'other', label: '기타' },
  ]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 dark:bg-black/70 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-[#191f28] dark:text-white" style={{ letterSpacing: '-0.02em' }}>
            새 지식 추가
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="닫기"
          >
            <X size={20} className="text-[#8b95a1] dark:text-gray-400" />
          </button>
        </div>

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="p-6 space-y-5">
            {/* 에러 메시지 */}
            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* 제목 */}
            <div>
              <label className="block text-sm font-semibold text-[#191f28] dark:text-white mb-2">
                제목 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-[#191f28] dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                placeholder="지식 항목의 제목을 입력하세요"
                maxLength={500}
                required
              />
            </div>

            {/* 내용 */}
            <div>
              <label className="block text-sm font-semibold text-[#191f28] dark:text-white mb-2">
                내용 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-[#191f28] dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none"
                placeholder="지식 내용을 입력하세요. 마크다운 형식을 지원합니다."
                rows={8}
                required
              />
            </div>

            {/* 카테고리 */}
            <div>
              <label className="block text-sm font-semibold text-[#191f28] dark:text-white mb-2">
                카테고리
              </label>
              <select
                value={formData.category || ''}
                onChange={(e) => setFormData({ ...formData, category: e.target.value || null })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-[#191f28] dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              >
                {categoryOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                선택하지 않으면 AI가 자동으로 분류합니다.
              </p>
            </div>

            {/* 태그 */}
            <div>
              <label className="block text-sm font-semibold text-[#191f28] dark:text-white mb-2">
                태그
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-[#191f28] dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  placeholder="태그를 입력하고 Enter를 누르세요"
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="px-4 py-3 bg-gray-100 dark:bg-gray-800 text-[#191f28] dark:text-white rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                >
                  <Plus size={20} />
                </button>
              </div>
              {formData.tags && formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-primary-50 dark:bg-primary-500/10 text-primary-500 dark:text-primary-400 rounded-lg text-sm font-medium"
                    >
                      <TagIcon size={14} />
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-primary-600 dark:hover:text-primary-400"
                      >
                        <X size={14} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                태그를 지정하지 않으면 AI가 자동으로 추출합니다.
              </p>
            </div>

            {/* 작성자 */}
            <div>
              <label className="block text-sm font-semibold text-[#191f28] dark:text-white mb-2">
                작성자
              </label>
              <input
                type="text"
                value={formData.author || ''}
                onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-[#191f28] dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                placeholder="작성자 이름 (선택사항)"
              />
            </div>

            {/* 상태 */}
            <div>
              <label className="block text-sm font-semibold text-[#191f28] dark:text-white mb-2">
                상태
              </label>
              <div className="flex gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
                    value="published"
                    checked={formData.status === 'published'}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as 'published' | 'draft' })}
                    className="w-4 h-4 text-primary-500 focus:ring-primary-500 focus:ring-2"
                  />
                  <span className="text-sm text-[#4e5968] dark:text-gray-300">게시</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
                    value="draft"
                    checked={formData.status === 'draft'}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as 'published' | 'draft' })}
                    className="w-4 h-4 text-primary-500 focus:ring-primary-500 focus:ring-2"
                  />
                  <span className="text-sm text-[#4e5968] dark:text-gray-300">임시저장</span>
                </label>
              </div>
            </div>
          </div>

          {/* 푸터 */}
          <div className="flex gap-3 px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-[#191f28] dark:text-white rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-all font-semibold focus:outline-none focus:ring-2 focus:ring-gray-400"
              disabled={loading}
            >
              취소
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 active:bg-primary-700 transition-all font-semibold focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-300 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? '생성 중...' : '생성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
