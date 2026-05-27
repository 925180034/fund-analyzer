<template>
  <div class="page">
    <!-- 返回按钮 -->
    <div class="back-bar" @click="goBack">
      <span>‹</span>
      <span>返回</span>
    </div>

    <div v-if="loading" class="ios-loading">加载中...</div>

    <template v-else-if="fund">
      <!-- 基金基本信息 -->
      <div class="ios-card">
        <div class="fund-header">
          <div class="fund-name">{{ fund.name }}</div>
          <div class="fund-code">{{ fund.code }} · {{ fund.type }}</div>
        </div>
        <div class="fund-nav">
          <div class="nav-value" :class="fund.change >= 0 ? 'price-up' : 'price-down'">
            {{ fund.nav }}
          </div>
          <div class="nav-change" :class="fund.change >= 0 ? 'price-up' : 'price-down'">
            {{ fund.change >= 0 ? '+' : '' }}{{ fund.change }}%
          </div>
        </div>
        <div class="nav-date">净值日期: {{ fund.nav_date }}</div>
      </div>

      <!-- 阶段收益 -->
      <div class="ios-card">
        <div class="ios-card-header">阶段收益</div>
        <div class="ios-stats">
          <div class="ios-stat-item">
            <div class="ios-stat-label">近1月</div>
            <div class="ios-stat-value" :class="(fund.month1 ?? 0) >= 0 ? 'price-up' : 'price-down'">
              {{ fund.month1 != null ? (fund.month1 > 0 ? '+' : '') + fund.month1 + '%' : '--' }}
            </div>
          </div>
          <div class="ios-stat-item">
            <div class="ios-stat-label">近3月</div>
            <div class="ios-stat-value" :class="(fund.month3 ?? 0) >= 0 ? 'price-up' : 'price-down'">
              {{ fund.month3 != null ? (fund.month3 > 0 ? '+' : '') + fund.month3 + '%' : '--' }}
            </div>
          </div>
          <div class="ios-stat-item">
            <div class="ios-stat-label">近6月</div>
            <div class="ios-stat-value" :class="(fund.month6 ?? 0) >= 0 ? 'price-up' : 'price-down'">
              {{ fund.month6 != null ? (fund.month6 > 0 ? '+' : '') + fund.month6 + '%' : '--' }}
            </div>
          </div>
          <div class="ios-stat-item">
            <div class="ios-stat-label">近1年</div>
            <div class="ios-stat-value" :class="(fund.year1 ?? 0) >= 0 ? 'price-up' : 'price-down'">
              {{ fund.year1 != null ? (fund.year1 > 0 ? '+' : '') + fund.year1 + '%' : '--' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 净值走势 -->
      <div class="ios-card">
        <div class="ios-card-header">净值走势</div>
        <div class="ios-card-body">
          <div ref="chartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- 基金信息 -->
      <div class="ios-list">
        <div class="ios-list-item">
          <div class="item-content">
            <div class="item-title">基金公司</div>
          </div>
          <div class="item-value">{{ fund.company || '--' }}</div>
        </div>
        <div class="ios-list-item">
          <div class="item-content">
            <div class="item-title">基金经理</div>
          </div>
          <div class="item-value">{{ fund.manager || '--' }}</div>
        </div>
        <div class="ios-list-item">
          <div class="item-content">
            <div class="item-title">累计净值</div>
          </div>
          <div class="item-value">{{ fund.acc_nav || '--' }}</div>
        </div>
      </div>
    </template>

    <div v-else class="ios-empty">
      <div class="empty-icon">😕</div>
      <div class="empty-text">未找到基金信息</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getFundDetail } from '../api/fund'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

const fund = ref(null)
const loading = ref(true)
const chartRef = ref(null)

const goBack = () => router.push('/search')

onMounted(async () => {
  const code = route.params.code
  try {
    const res = await getFundDetail(code)
    fund.value = res.data
    
    if (fund.value?.nav_history?.length > 0) {
      await nextTick()
      renderChart()
    }
  } catch (err) {
    console.error('获取详情失败:', err)
  } finally {
    loading.value = false
  }
})

const renderChart = () => {
  if (!chartRef.value || !fund.value?.nav_history) return
  
  const chart = echarts.init(chartRef.value)
  const history = fund.value.nav_history
  
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { top: 10, right: 10, bottom: 30, left: 50 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E5EA',
      textStyle: { color: '#1C1C1E', fontSize: 13 },
      formatter: (params) => {
        const p = params[0]
        return `${p.axisValue}<br/>净值: <b>${p.value}</b>`
      }
    },
    xAxis: {
      type: 'category',
      data: history.map(h => h.date),
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
    series: [{
      data: history.map(h => h.nav),
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
    }]
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

.back-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--ios-blue);
  font-size: 17px;
  margin-bottom: 16px;
  cursor: pointer;
}

.back-bar span:first-child {
  font-size: 24px;
  line-height: 1;
}

.fund-header {
  padding: 16px;
}

.fund-name {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.fund-code {
  font-size: 13px;
  color: var(--ios-text3);
  margin-top: 4px;
}

.fund-nav {
  padding: 0 16px 12px;
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.nav-value {
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -0.8px;
}

.nav-change {
  font-size: 18px;
  font-weight: 500;
}

.nav-date {
  padding: 0 16px 16px;
  font-size: 13px;
  color: var(--ios-text3);
}

.chart-container {
  height: 250px;
  width: 100%;
}
</style>
