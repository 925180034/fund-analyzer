import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 搜索基金
export function searchFund(keyword) {
  return api.get('/fund/search', { params: { keyword } })
}

// 获取基金详情
export function getFundDetail(code) {
  return api.get(`/fund/detail/${code}`)
}

// 获取基金净值历史
export function getFundNav(code) {
  return api.get(`/fund/nav/${code}`)
}

// 获取基金排行
export function getFundRanking(fundType = '全部', page = 1, size = 20) {
  return api.get('/fund/ranking', { params: { fund_type: fundType, page, size } })
}

// 普通定投回测
export function backtestRegular(params) {
  return api.get('/backtest/regular', { params })
}

// 均线智能定投回测
export function backtestSmartMa(params) {
  return api.get('/backtest/smart-ma', { params })
}

// 回撤加仓定投回测
export function backtestDrawdown(params) {
  return api.get('/backtest/drawdown', { params })
}

// 创建组合
export function createPortfolio(data) {
  return api.post('/portfolio/create', data)
}

// 获取组合列表
export function getPortfolioList() {
  return api.get('/portfolio/list')
}

// 获取组合详情
export function getPortfolio(id) {
  return api.get(`/portfolio/${id}`)
}

// 删除组合
export function deletePortfolio(id) {
  return api.delete(`/portfolio/${id}`)
}

// 分析组合
export function analyzePortfolio(id) {
  return api.get(`/portfolio/${id}/analysis`)
}

// 添加持仓
export function addHolding(data) {
  return api.post('/monitor/add', data)
}

// 获取持仓列表
export function getHoldings() {
  return api.get('/monitor/holdings')
}

// 获取风险提醒
export function getAlerts() {
  return api.get('/monitor/alerts')
}

// 基金诊断报告
export function getFundReport(code) {
  return api.get(`/report/fund/${code}`)
}

// 基金经理分析
export function getManagerAnalysis(name) {
  return api.get(`/fund/manager/${name}`)
}

export default api
