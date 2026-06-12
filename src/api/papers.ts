/**
 * 论文 API 调用封装
 */
import api from './index'
import type { AxiosResponse } from 'axios'

// ========== 类型定义 ==========

export interface PaperCreate {
  title: string
  authors?: string[]
  abstract?: string
  doi?: string
  arxiv_id?: string
  year?: number
  journal?: string
  source_url?: string
  tags?: string[]
  notes?: string
  collection?: string
}

export interface PaperUpdate {
  tags?: string[]
  notes?: string
  collection?: string
}

export interface PaperResponse {
  id: string
  title: string
  authors: string[]
  abstract: string | null
  doi: string | null
  arxiv_id: string | null
  source: string
  source_url: string | null
  year: number | null
  journal: string | null
  citation_count: number
  pages_count: number | null
  tags: string[]
  notes: string | null
  collection: string
  added_at: string | null
  created_at: string
  updated_at: string
}

export interface PaperDetailResponse extends PaperResponse {
  full_text: string | null
  file_path: string | null
  chunks_count: number
  has_summary: boolean
}

export interface PaginatedResponse {
  items: PaperResponse[]
  total: number
  page: number
  size: number
}

export interface UploadResponse {
  paper_id: string
  title: string
  authors: string[]
  abstract: string | null
  file_path: string
  pages_count: number | null
}

export interface PaperListParams {
  page?: number
  size?: number
  sort?: string
  order?: string
  collection?: string
  tag?: string
  keyword?: string
}

// ========== API 方法 ==========

/** 获取论文列表 */
export function getPapers(params?: PaperListParams): Promise<AxiosResponse<PaginatedResponse>> {
  return api.get('/papers', { params })
}

/** 获取论文详情 */
export function getPaper(id: string): Promise<AxiosResponse<PaperDetailResponse>> {
  return api.get(`/papers/${id}`)
}

/** 手动创建论文 */
export function createPaper(data: PaperCreate): Promise<AxiosResponse<PaperResponse>> {
  return api.post('/papers', data)
}

/** 更新论文用户关联信息 */
export function updatePaper(id: string, data: PaperUpdate): Promise<AxiosResponse<PaperResponse>> {
  return api.patch(`/papers/${id}`, data)
}

/** 删除论文 */
export function deletePaper(id: string): Promise<AxiosResponse<{ detail: string }>> {
  return api.delete(`/papers/${id}`)
}

/** 上传 PDF 论文 */
export function uploadPdf(file: File): Promise<AxiosResponse<UploadResponse>> {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload/pdf', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000, // 上传+解析可能需要较长时间
  })
}
