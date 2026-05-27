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

/**
 * 获取基金净值历史
 * @param {string} code - 基金代码
 * @param {string} startDate - 开始日期
 * @param {string} endDate - 结束日期
 * @returns {Promise} 净值历史数据
 */
export function getFundNav(code, startDate, endDate) {
  return api.get(`/fund/nav/${code}`, {
    params: { start_date: startDate, end_date: endDate }
  })
}

/**
 * 获取基金排行
 * @param {string} fundType - 基金类型
 * @param {string} sortBy - 排序字段
 * @param {number} page - 页码
 * @param {number} size - 每页数量
 * @returns {Promise} 排行数据
 */
export function getFundRanking(fundType = '全部', sortBy = 'rank_1y', page = 1, size = 20) {
  return api.get('/fund/ranking', {
    params: { fund_type: fundType, sort_by: sortBy, page, size }
  })
}

/**
 * 普通定投回测
 * @param {object} params - 回测参数
 * @returns {Promise} 回测结果
 */
export function backtestRegular(params) {
  return api.get('/backtest/regular', { params })
}

/**
 * 均线智能定投回测
 * @param {object} params - 回测参数
 * @returns {Promise} 回测结果
 */
export function backtestSmartMa(params) {
  return api.get('/backtest/smart-ma', { params })
}

/**
 * 回撤加仓定投回测
 * @param {object} params - 回测参数
 * @returns {Promise} 回测结果
 */
export function backtestDrawdown(params) {
  return api.get('/backtest/drawdown', { params })
}

/**
 * 4433筛选基金
 * @param {object} params - 筛选参数
 * @returns {Promise} 筛选结果
 */
export function screen4433(params) {
  return api.get('/screen/4433', { params })
}

export default api
