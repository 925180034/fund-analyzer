<template>
  <div class="page">
    <!-- 分段控件 -->
    <div class="ios-segment">
      <div 
        v-for="type in fundTypes" 
        :key="type"
        class="segment-item"
        :class="{ active: currentType === type }"
        @click="changeType(type)"
      >
        {{ type }}
      </div>
    </div>

    <div v-if="loading" class="ios-loading">加载中...</div>

    <div v-else-if="fundList.length === 0" class="ios-empty">
      <div class="empty-icon">📊</div>
      <div class="empty-text">暂无数据</div>
    </div>

    <div v-else class="ios-list">
      <div 
        v-for="(fund, index) in fundList" 
        :key="fund.code"
        class="ios-list-item"
        @click="goToDetail(fund.code)"
      >
        <div class="rank-number" :class="{ 'top-3': index < 3 }">{{ index + 1 }}</div>
        <div class="item-content">
          <div class="item-title">{{ fund.name }}</div>
          <div class="item-subtitle">{{ fund.code }} · {{ fund.type }}</div>
        </div>
        <div class="item-right">
          <div class="item-value">{{ fund.scale ? fund.scale.toFixed(2) + '亿' : '--' }}</div>
          <span class="item-arrow">›</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getFundRanking } from '../api/fund'

const router = useRouter()
const fundTypes = ['全部', '股票型', '混合型', '债券型', '指数型']
const currentType = ref('全部')
const fundList = ref([])
const loading = ref(false)

const loadRanking = async () => {
  loading.value = true
  try {
    const res = await getFundRanking(currentType.value)
    fundList.value = res.data?.data || []
  } catch (err) {
    console.error('获取排行失败:', err)
    fundList.value = []
  } finally {
    loading.value = false
  }
}

const changeType = (type) => {
  currentType.value = type
  loadRanking()
}

const goToDetail = (code) => {
  router.push(`/fund/${code}`)
}

onMounted(loadRanking)
</script>

<style scoped>
.page {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.rank-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--ios-gray6);
  color: var(--ios-text3);
  font-size: 13px;
  font-weight: 500;
  margin-right: 12px;
  flex-shrink: 0;
}

.rank-number.top-3 {
  background: var(--ios-orange);
  color: white;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
