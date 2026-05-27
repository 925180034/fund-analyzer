<template>
  <div class="page">
    <!-- 搜索框 -->
    <div class="ios-search">
      <span class="search-icon">🔍</span>
      <input 
        v-model="keyword" 
        placeholder="输入基金代码或名称" 
        @keyup.enter="handleSearch"
      />
    </div>

    <!-- 热门搜索 -->
    <div v-if="!hasSearched" class="ios-card">
      <div class="ios-card-header">热门搜索</div>
      <div class="ios-card-body">
        <div class="hot-tags">
          <span 
            v-for="tag in hotKeywords" 
            :key="tag" 
            class="ios-badge ios-badge-blue"
            @click="quickSearch(tag)"
          >
            {{ tag }}
          </span>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="hasSearched">
      <div v-if="loading" class="ios-loading">搜索中...</div>
      
      <div v-else-if="fundList.length === 0" class="ios-empty">
        <div class="empty-icon">📭</div>
        <div class="empty-text">未找到相关基金</div>
      </div>

      <div v-else class="ios-list">
        <div 
          v-for="fund in fundList" 
          :key="fund.code" 
          class="ios-list-item"
          @click="goToDetail(fund.code)"
        >
          <div class="item-content">
            <div class="item-title">{{ fund.name }}</div>
            <div class="item-subtitle">{{ fund.code }} · {{ fund.type }}</div>
          </div>
          <span class="item-arrow">›</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { searchFund } from '../api/fund'

const router = useRouter()
const keyword = ref('')
const fundList = ref([])
const loading = ref(false)
const hasSearched = ref(false)

const hotKeywords = ['110011', '005827', '161725', '易方达', '招商', '沪深300']

const handleSearch = async () => {
  const kw = keyword.value.trim()
  if (!kw) return
  
  loading.value = true
  hasSearched.value = true
  
  try {
    const res = await searchFund(kw)
    fundList.value = res.data?.data || []
  } catch (err) {
    console.error('搜索失败:', err)
    fundList.value = []
  } finally {
    loading.value = false
  }
}

const quickSearch = (tag) => {
  keyword.value = tag
  handleSearch()
}

const goToDetail = (code) => {
  router.push(`/fund/${code}`)
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

.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hot-tags .ios-badge {
  cursor: pointer;
  transition: transform 0.15s;
}

.hot-tags .ios-badge:active {
  transform: scale(0.95);
}
</style>
