import React, { useState, useEffect } from 'react';
import { Plus, Search, Tag, Filter, Edit, Trash2, FileText, BookOpen } from 'lucide-react';
import KnowledgeCreateModal from '../components/KnowledgeCreateModal';
import KnowledgeEditModal from '../components/KnowledgeEditModal';
import { KnowledgeCardSkeleton } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import { knowledgeService } from '../services/api';
import { useAuthStore } from '@/store/authStore';

interface KnowledgeEntry {
  id: number;
  title: string;
  category: string | null;
  tags: string[];
  source_type: string;
  author: string | null;
  status: string;
  created_at: string;
}

interface Category {
  id: number;
  name: string;
  description: string | null;
  color: string | null;
  icon: string | null;
  display_order: number;
}

const KnowledgePage: React.FC = () => {
  const token = useAuthStore((s) => s.token);
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedTags] = useState<string[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingEntryId, setEditingEntryId] = useState<number | null>(null);

  // 지식 항목 로드 (인증 토큰 포함)
  const loadEntries = async () => {
    try {
      setLoading(true);
      const params: { category?: string; tags?: string } = {};
      if (selectedCategory) params.category = selectedCategory;
      if (selectedTags.length > 0) params.tags = selectedTags.join(',');
      const data = await knowledgeService.listKnowledgeEntries(params);
      setEntries(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load knowledge entries:', error);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  };

  // 카테고리 로드 (인증 토큰 포함)
  const loadCategories = async () => {
    try {
      const data = await knowledgeService.listCategories();
      setCategories(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load categories:', error);
      setCategories([]);
    }
  };

  useEffect(() => {
    if (!token) return;
    loadEntries();
    loadCategories();
  }, [token, selectedCategory, selectedTags]);

  // 지식 항목 삭제
  const handleDelete = async (id: number) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;
    
    try {
      await knowledgeService.deleteKnowledgeEntry(id);
      loadEntries();
    } catch (error) {
      console.error('Failed to delete entry:', error);
    }
  };

  // 편집 모달 열기
  const handleEdit = (id: number) => {
    setEditingEntryId(id);
    setShowEditModal(true);
  };

  // 모달 성공 콜백
  const handleModalSuccess = () => {
    loadEntries();
  };

  // 카테고리 배지 색상
  const getCategoryColor = (category: string | null) => {
    const colors: { [key: string]: string } = {
      'error_fix': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      'tech_share': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'how_to': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'best_practice': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      'other': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
    };
    return colors[category || 'other'] || colors.other;
  };

  // 필터링된 항목 (entries가 배열이 아닐 경우 방어 처리)
  const filteredEntries = (Array.isArray(entries) ? entries : []).filter(entry =>
    entry.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (entry.tags ?? []).some(tag => tag?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* 헤더 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-soft">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ letterSpacing: '-0.02em' }}>
                  지식 관리
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  회사 내부 기술 지식을 관리하고 검색하세요
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 active:bg-primary-700 transition-all shadow-soft hover:shadow-soft-lg min-h-[44px] font-semibold"
            >
              <Plus className="w-5 h-5" />
              <span className="hidden sm:inline">새 지식 추가</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          {/* 사이드바 - 필터 */}
          <div className="w-64 flex-shrink-0">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Filter className="w-4 h-4" />
                필터
              </h2>
              
              {/* 카테고리 필터 */}
              <div className="mb-4">
                <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                  카테고리
                </h3>
                <div className="space-y-1">
                  <button
                    onClick={() => setSelectedCategory(null)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all min-h-[40px] ${
                      selectedCategory === null
                        ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-500 dark:text-primary-400 font-medium shadow-soft'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    전체
                  </button>
                  {['error_fix', 'tech_share', 'how_to', 'best_practice', 'other'].map(cat => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all min-h-[40px] ${
                        selectedCategory === cat
                          ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-500 dark:text-primary-400 font-medium shadow-soft'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      {cat === 'error_fix' ? '에러 해결' :
                       cat === 'tech_share' ? '기술 공유' :
                       cat === 'how_to' ? '사용법' :
                       cat === 'best_practice' ? '모범 사례' : '기타'}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 메인 콘텐츠 */}
          <div className="flex-1">
            {/* 검색 바 */}
            <div className="mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="지식 검색..."
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                />
              </div>
            </div>

            {/* 지식 항목 그리드 */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <KnowledgeCardSkeleton key={i} />
                ))}
              </div>
            ) : filteredEntries.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="지식 항목이 없습니다"
                description="첫 번째 지식을 추가하여 팀의 지식베이스를 구축하세요."
                action={{
                  label: '새 지식 추가',
                  onClick: () => setShowCreateModal(true),
                }}
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredEntries.map((entry) => (
                  <div
                    key={entry.id}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow-soft border border-gray-200 dark:border-gray-700 p-4 hover:shadow-soft-lg transition-all duration-200 animate-slide-up"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white line-clamp-2 flex-1">
                        {entry.title}
                      </h3>
                      <div className="flex gap-1 ml-2">
                        <button
                          onClick={() => handleEdit(entry.id)}
                          className="min-w-[36px] min-h-[36px] flex items-center justify-center text-gray-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-500/10 rounded-lg transition-all"
                          title="편집"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(entry.id)}
                          className="min-w-[36px] min-h-[36px] flex items-center justify-center text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                          title="삭제"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 mb-3">
                      {entry.category && (
                        <span className={`text-xs px-2 py-1 rounded-md font-medium ${getCategoryColor(entry.category)}`}>
                          {entry.category === 'error_fix' ? '에러 해결' :
                           entry.category === 'tech_share' ? '기술 공유' :
                           entry.category === 'how_to' ? '사용법' :
                           entry.category === 'best_practice' ? '모범 사례' : '기타'}
                        </span>
                      )}
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {entry.source_type}
                      </span>
                    </div>
                    
                    {entry.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {entry.tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md"
                          >
                            <Tag className="w-3 h-3" />
                            {tag}
                          </span>
                        ))}
                        {entry.tags.length > 3 && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            +{entry.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(entry.created_at).toLocaleDateString('ko-KR')}
                      {entry.author && ` · ${entry.author}`}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 모달 */}
      <KnowledgeCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleModalSuccess}
      />
      <KnowledgeEditModal
        isOpen={showEditModal}
        entryId={editingEntryId}
        onClose={() => {
          setShowEditModal(false);
          setEditingEntryId(null);
        }}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
};

export default KnowledgePage;
