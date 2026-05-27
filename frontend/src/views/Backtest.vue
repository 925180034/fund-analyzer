<template>
  <div class="page">
    <!-- 回测表单 -->
    <div class="ios-card">
      <div class="ios-card-header">定投回测</div>
      <div class="ios-card-body">
        <div class="form-group">
          <label>基金代码</label>
          <input v-model="form.code" class="ios-input" placeholder="如 110011" />
        </div>
        <div class="form-group">
          <label>每期金额 (元)</label>
          <input v-model.number="form.amount" class="ios-input" type="number" placeholder="1000" />
        </div>
        <div class="form-group">
          <label>投资策略</label>
          <div class="ios-segment">
            <div 
              v-for="s in strategies" 
              :key="s.value"
              class="segment-item"
              :class="{ active: form.strategy === s.value }"
              @click="form.strategy = s.value"
            >
              {{ s.label }}
            </div>
          </div>
        </div>
        <div class="form-group">
          <label>开始日期</label>
          <input v-model="form.startDate" class="ios-input" type="date" />
        </div>
        <button class="ios-btn ios-btn-primary" @click="runBacktest" :disabled="loading">
          {{ loading ? '回测中...' : '开始回测' }}
        </button>
      </div>
    </div>

    <!-- 回测结果 -->
    <template v-if="result">
      <div class="ios-card">
        <div class="ios-card-header">回测结果</div>
        <div class="ios-stats">
          <div class="ios-stat-item">
            <div class="ios-stat-label">总投入</div>
            <div class="ios-stat-value">{{ result.summary?.total_invest?.toLocaleString() }}元</div>
          </div>
          <div class="ios-stat-item">
            <div class="ios-stat-label">最终价值</div>
            <div class="ios-stat-value">{{ result.summary?.final_value?.toLocaleString() }}元</div>
          </div>
          <div class="ios-stat-item">
            <div class="ios-stat-label">总收益</div>
            <div class="ios-stat-value" :class="(result.summary?.total_profit ?? 0) >= 0 ? 'price-up' : 'price-down'">
              {{ result.summary?.total_profit?.toLocaleString() }}元
            </div>
          </div>
          <div class="ios-stat-item">
            <div class="ios-stat-label">收益率</div>
            <div class="ios-stat-value" :class="(result.summary?.total_return ?? 0) >= 0 ? 'price-up' : 'price-down'">
              {{ result.summary?.total_return }}%
            </div>
          </div>
        </div>
      </div>

      <!-- 走势图 -->
      <div class="ios-card">
        <div class="ios-card-header">资产走势</div>
        <div class="ios-card-body">
          <div ref="chartRef" class="chart-container"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { backtestRegular, backtestSmartMa, backtestDrawdown } from '../api/fund'
import * as echarts from 'echarts'

const form = ref({
  code: '',
  amount: 1000,
  strategy: 'regular',
  startDate: '2020-01-01'
})

const strategies = [
  { label: '普通定投', value: 'regular' },
  { label: '均线智能', value: 'smart-ma' },
  { label: '回撤加仓', value: 'drawdown' }
]

const loading = ref(false)
const result = ref(null)
const chartRef = ref(null)

const runBacktest = async () => {
  if (!form.value.code) return
  
  loading.value = true
  result.value = null
  
  try {
    const params = {
      code: form.value.code,
      amount: form.value.amount,
      start_date: form.value.startDate
    }
    
    let res
    switch (form.value.strategy) {
      case 'regular':
        res = await backtestRegular(params)
        break
      case 'smart-ma':
        res = await backtestSmartMa(params)
        break
      case 'drawdown':
        res = await backtestDrawdown(params)
        break
    }
    
    result.value = res.data?.data || res.data
    
    if (result.value?.records?.length > 0) {
      await nextTick()
      renderChart()
    }
  } catch (err) {
    console.error('回测失败:', err)
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || !result.value?.records) return
  
  const chart = echarts.init(chartRef.value)
  const records = result.value.records
  
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { top: 10, right: 10, bottom: 30, left: 60 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E5EA',
      textStyle: { color: '#1C1C1E', fontSize: 13 }
    },
    xAxis: {
      type: 'category',
      data: records.map(r => r.date),
      axisLine: { lineStyle: { color: '#E5E5EA' } },
      axisLabel: { color: '#8E8E93', fontSize: 11 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#8E8E93', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F2F2F7' } }
    },
    series: [
      {
        name: '资产价值',
        data: records.map(r => r.total_value),
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#007AFF', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,122,255,0.15)' },
            { offset: 1, color: 'rgba(0,122,255,0)' }
          ])
        }
      },
      {
        name: '累计投入',
        data: records.map(r => r.total_invest),
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#8E8E93', width: 1, type: 'dashed' }
      }
    ]
  })
}
</script>

<style scoped>
.page {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: var(--ios-text3);
  margin-bottom: 6px;
}

.chart-container {
  height: 280px;
  width: 100%;
}
</style>
