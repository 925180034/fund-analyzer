<template>
  <div class="fund-detail" v-loading="loading">
    <el-page-header @back="goBack" :content="fundInfo.name || '基金详情'" />

    <el-row :gutter="20" class="info-row">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ fundInfo.name }} ({{ fundInfo.code }})</span>
              <el-tag v-if="fundInfo.type" type="info" size="small">{{ fundInfo.type }}</el-tag>
            </div>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="基金代码">{{ fundInfo.code }}</el-descriptions-item>
            <el-descriptions-item label="基金类型">{{ fundInfo.type || '--' }}</el-descriptions-item>
            <el-descriptions-item label="最新净值">
              <span :class="fundInfo.nav >= 0 ? 'price-up' : 'price-down'">
                {{ fundInfo.nav ?? '--' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="日涨跌幅">
              <span :class="fundInfo.change >= 0 ? 'price-up' : 'price-down'">
                {{ fundInfo.change != null ? (fundInfo.change > 0 ? '+' : '') + fundInfo.change + '%' : '--' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="累计净值">{{ fundInfo.accNav ?? '--' }}</el-descriptions-item>
            <el-descriptions-item label="净值日期">{{ fundInfo.navDate ?? '--' }}</el-descriptions-item>
            <el-descriptions-item label="基金经理" :span="2">{{ fundInfo.manager || '--' }}</el-descriptions-item>
            <el-descriptions-item label="基金公司" :span="2">{{ fundInfo.company || '--' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>📈 关键指标</span>
          </template>
          <div class="stats-list">
            <div class="stat-item">
              <span class="stat-label">近1月</span>
              <span :class="(fundStats.month1 ?? 0) >= 0 ? 'price-up' : 'price-down'">
                {{ fundStats.month1 != null ? (fundStats.month1 > 0 ? '+' : '') + fundStats.month1 + '%' : '--' }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">近3月</span>
              <span :class="(fundStats.month3 ?? 0) >= 0 ? 'price-up' : 'price-down'">
                {{ fundStats.month3 != null ? (fundStats.month3 > 0 ? '+' : '') + fundStats.month3 + '%' : '--' }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">近6月</span>
              <span :class="(fundStats.month6 ?? 0) >= 0 ? 'price-up' : 'price-down'">
                {{ fundStats.month6 != null ? (fundStats.month6 > 0 ? '+' : '') + fundStats.month6 + '%' : '--' }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">近1年</span>
              <span :class="(fundStats.year1 ?? 0) >= 0 ? 'price-up' : 'price-down'">
                {{ fundStats.year1 != null ? (fundStats.year1 > 0 ? '+' : '') + fundStats.year1 + '%' : '--' }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">近3年</span>
              <span :class="(fundStats.year3 ?? 0) >= 0 ? 'price-up' : 'price-down'">
                {{ fundStats.year3 != null ? (fundStats.year3 > 0 ? '+' : '') + fundStats.year3 + '%' : '--' }}
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>📊 单位净值走势</span>
          <el-radio-group v-model="chartPeriod" size="small" @change="updateChart">
            <el-radio-button label="1m">近1月</el-radio-button>
            <el-radio-button label="3m">近3月</el-radio-button>
            <el-radio-button label="6m">近6月</el-radio-button>
            <el-radio-button label="1y">近1年</el-radio-button>
            <el-radio-button label="all">全部</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getFundDetail } from '../api/fund'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const fundInfo = ref({})
const fundStats = ref({})
const navHistory = ref([])
const chartPeriod = ref('6m')
const chartRef = ref(null)

let chartInstance = null

const goBack = () => {
  router.push('/search')
}

const fetchDetail = async () => {
  const code = route.params.code
  loading.value = true

  try {
    const res = await getFundDetail(code)
    const data = res.data

    fundInfo.value = {
      code: data.code || code,
      name: data.name || '',
      type: data.type || '',
      nav: data.nav,
      change: data.change,
      accNav: data.acc_nav,
      navDate: data.nav_date,
      manager: data.manager || '',
      company: data.company || ''
    }

    fundStats.value = {
      month1: data.month1,
      month3: data.month3,
      month6: data.month6,
      year1: data.year1,
      year3: data.year3
    }

    navHistory.value = data.nav_history || []

    await nextTick()
    initChart()
  } catch (err) {
    console.error('获取基金详情失败:', err)
    ElMessage.error('获取基金详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const getFilteredHistory = () => {
  const history = navHistory.value
  if (!history || history.length === 0) return { dates: [], values: [] }

  const now = new Date()
  let startDate = new Date(0)

  switch (chartPeriod.value) {
    case '1m':
      startDate = new Date(now)
      startDate.setMonth(startDate.getMonth() - 1)
      break
    case '3m':
      startDate = new Date(now)
      startDate.setMonth(startDate.getMonth() - 3)
      break
    case '6m':
      startDate = new Date(now)
      startDate.setMonth(startDate.getMonth() - 6)
      break
    case '1y':
      startDate = new Date(now)
      startDate.setFullYear(startDate.getFullYear() - 1)
      break
    case 'all':
    default:
      startDate = new Date(0)
  }

  const filtered = history.filter(item => new Date(item.date) >= startDate)

  return {
    dates: filtered.map(item => item.date),
    values: filtered.map(item => item.nav)
  }
}

const initChart = () => {
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  const { dates, values } = getFilteredHistory()

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        return `${p.axisValue}<br/>单位净值: <b>${p.value}</b>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 30,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [
      {
        name: '单位净值',
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#667eea',
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102,126,234,0.3)' },
            { offset: 1, color: 'rgba(102,126,234,0.02)' }
          ])
        }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

onMounted(() => {
  fetchDetail()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}
</script>

<style scoped>
.fund-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.info-row {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}

.chart-card {
  margin-top: 20px;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.price-up {
  color: #f56c6c;
  font-weight: 600;
}

.price-down {
  color: #67c23a;
  font-weight: 600;
}
</style>
