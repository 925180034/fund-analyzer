<template>
  <div class="fund-search">
    <el-card class="search-card">
      <template #header>
        <div class="card-header">
          <span>🔍 基金搜索</span>
        </div>
      </template>

      <el-input
        v-model="keyword"
        placeholder="请输入基金代码或名称，如：110011 或 易方达"
        size="large"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" :loading="loading">
            搜索
          </el-button>
        </template>
      </el-input>

      <div class="hot-keywords" v-if="!hasSearched">
        <p>热门搜索：</p>
        <el-tag
          v-for="tag in hotKeywords"
          :key="tag"
          class="hot-tag"
          @click="quickSearch(tag)"
          effect="plain"
          round
        >
          {{ tag }}
        </el-tag>
      </div>
    </el-card>

    <el-card v-if="hasSearched" class="result-card">
      <template #header>
        <div class="card-header">
          <span>搜索结果 ({{ fundList.length }} 条)</span>
        </div>
      </template>

      <el-table
        v-if="fundList.length > 0"
        :data="fundList"
        stripe
        highlight-current-row
        @row-click="goToDetail"
        style="width: 100%"
      >
        <el-table-column prop="code" label="基金代码" width="120" />
        <el-table-column prop="name" label="基金名称" min-width="200" />
        <el-table-column prop="type" label="基金类型" width="120" />
        <el-table-column label="最新净值" width="120">
          <template #default="{ row }">
            <span :class="row.nav >= 0 ? 'price-up' : 'price-down'">
              {{ row.nav ?? '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="日涨跌幅" width="120">
          <template #default="{ row }">
            <span :class="row.change >= 0 ? 'price-up' : 'price-down'">
              {{ row.change != null ? (row.change > 0 ? '+' : '') + row.change + '%' : '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="goToDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="未找到相关基金" />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { searchFund } from '../api/fund'
import { ElMessage } from 'element-plus'

const router = useRouter()
const keyword = ref('')
const fundList = ref([])
const loading = ref(false)
const hasSearched = ref(false)

const hotKeywords = ['110011', '000001', '161725', '易方达', '招商', '白酒']

const handleSearch = async () => {
  const kw = keyword.value.trim()
  if (!kw) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  hasSearched.value = true

  try {
    const res = await searchFund(kw)
    fundList.value = res.data || []
  } catch (err) {
    console.error('搜索失败:', err)
    ElMessage.error('搜索失败，请稍后重试')
    fundList.value = []
  } finally {
    loading.value = false
  }
}

const quickSearch = (tag) => {
  keyword.value = tag
  handleSearch()
}

const goToDetail = (row) => {
  router.push(`/fund/${row.code}`)
}
</script>

<style scoped>
.fund-search {
  max-width: 1000px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.hot-keywords {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.hot-keywords p {
  color: #909399;
  font-size: 14px;
}

.hot-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.hot-tag:hover {
  color: #409eff;
  border-color: #409eff;
}

.result-card {
  margin-bottom: 20px;
}

.price-up {
  color: #f56c6c;
  font-weight: 600;
}

.price-down {
  color: #67c23a;
  font-weight: 600;
}

:deep(.el-table) {
  cursor: pointer;
}
</style>
