import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

/**
 * 搜索基金
 * @param {string} keyword - 搜索关键词（基金代码或名称）
 * @returns {Promise} 搜索结果列表
 */
export function searchFund(keyword) {
  return api.get('/fund/search', {
    params: { keyword }
  })
}

/**
 * 获取基金详情
 * @param {string} code - 基金代码
 * @returns {Promise} 基金详情数据（含净值历史）
 */
export function getFundDetail(code) {
  return api.get(`/fund/${code}`)
}

export default api
