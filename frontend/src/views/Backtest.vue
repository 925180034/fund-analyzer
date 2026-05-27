<template>
  <div class="backtest-page">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>📈 定投回测</span>
        </div>
      </template>

      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="基金代码" prop="code">
              <el-input v-model="form.code" placeholder="如 110011" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="定投金额" prop="amount">
              <el-input-number v-model="form.amount" :min="100" :step="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="策略" prop="strategy">
              <el-select v-model="form.strategy" style="width:100%">
                <el-option label="普通定投" value="regular" />
                <el-option label="均线智能定投" value="smart-ma" />
                <el-option label="回撤加仓定投" value="drawdown" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="开始日期">
              <el-date-picker v-model="form.startDate" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8" v-if="form.strategy === 'smart-ma'">
            <el-form-item label="均线周期">
              <el-input-number v-model="form.maPeriod" :min="20" :max="500" :step="10" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8" v-if="form.strategy === 'drawdown'">
            <el-form-item label="回撤阈值">
              <el-input-number v-model="form.threshold" :min="-0.5" :max="-0.01" :step="0.01" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8" v-if="form.strategy === 'drawdown'">
            <el-form-item label="加仓倍数">
              <el-input-number v-model="form.extraRatio" :min="1" :max="5" :step="0.5" :precision="1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" @click="handleBacktest" :loading="loading" style="width:100%">
                开始回测
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 回测结果指标 -->
    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="card-header">
          <span>📊 回测结果 - {{ result.strategy }}</span>
        </div>
      </template>

      <el-row :gutter="20" class="metrics-row">
        <el-col :span="4">
          <div class="metric-item">
            <div class="metric-label">投入次数</div>
            <div class="metric-value">{{ result.invest_count }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="metric-item">
            <div class="metric-label">总投入</div>
            <div class="metric-value">¥{{ formatNum(result.total_invested) }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="metric-item">
            <div class="metric-label">最终市值</div>
            <div class="metric-value">¥{{ formatNum(result.final_value) }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="metric-item">
            <div class="metric-label">总收益</div>
            <div class="metric-value" :class="result.total_profit >= 0 ? 'price-up' : 'price-down'">
              ¥{{ formatNum(result.total_profit) }}
            </div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="metric-item">
            <div class="metric-label">总收益率</div>
            <div class="metric-value" :class="result.total_return >= 0 ? 'price-up' : 'price-down'">
              {{ result.total_return }}%
            </div>
          </div>
        </el-col>
        <el-col :span="4" v-if="result.extra_count !== undefined">
          <div class="metric-item">
            <div class="metric-label">加仓次数</div>
            <div class="metric-value">{{ result.extra_count }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 资产走势图 -->
    <el-card v-if="result && result.records" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>📈 资产走势</span>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { backtestRegular, backtestSmartMa, backtestDrawdown } from '../api/fund'
import * as echarts from 'echarts'

const formRef = ref(null)
const chartRef = ref(null)
const loading = ref(false)
const result = ref(null)
let chartInstance = null

const form = ref({
  code: '',
  amount: 1000,
  strategy: 'regular',
  startDate: '',
  maPeriod: 250,
  threshold: -0.1,
  extraRatio: 2.0
})

const rules = {
  code: [{ required: true, message: '请输入基金代码', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入定投金额', trigger: 'blur' }],
  strategy: [{ required: true, message: '请选择策略', trigger: 'change' }]
}

const formatNum = (num) => {
  if (num == null) return '--'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const handleBacktest = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  result.value = null

  try {
    const baseParams = {
      code: form.value.code,
      amount: form.value.amount,
      start_date: form.value.startDate || undefined
    }

    let res
    switch (form.value.strategy) {
      case 'regular':
        res = await backtestRegular(baseParams)
        break
      case 'smart-ma':
        res = await backtestSmartMa({ ...baseParams, ma_period: form.value.maPeriod })
        break
      case 'drawdown':
        res = await backtestDrawdown({
          ...baseParams,
          threshold: form.value.threshold,
          extra_ratio: form.value.extraRatio
        })
        break
    }

    if (res.data.error) {
      ElMessage.error(res.data.error)
      return
    }

    result.value = res.data.data || res.data
    await nextTick()
    renderChart()
  } catch (err) {
    console.error('回测失败:', err)
    ElMessage.error('回测失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || !result.value?.records) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)

  const records = result.value.records
  const dates = records.map(r => r.date)
  const invested = records.map(r => r.total_invested)
  const values = records.map(r => r.current_value)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let html = `<div style="font-weight:bold;margin-bottom:5px">${params[0].axisValue}</div>`
        params.forEach(p => {
          html += `<div>${p.marker} ${p.seriesName}: ¥${Number(p.value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</div>`
        })
        return html
      }
    },
    legend: {
      data: ['累计投入', '资产市值'],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 30,
        formatter: (val) => val.substring(0, 7)
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (val) => '¥' + (val / 10000).toFixed(0) + '万'
      }
    },
    series: [
      {
        name: '累计投入',
        type: 'line',
        data: invested,
        smooth: true,
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.1 },
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '资产市值',
        type: 'line',
        data: values,
        smooth: true,
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.1 },
        itemStyle: { color: '#67C23A' }
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance?.resize()
}

window.addEventListener('resize', handleResize)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.backtest-page {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.form-card {
  margin-bottom: 20px;
}

.result-card {
  margin-bottom: 20px;
}

.metrics-row {
  text-align: center;
}

.metric-item {
  padding: 12px 0;
}

.metric-label {
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 400px;
}
</style>
