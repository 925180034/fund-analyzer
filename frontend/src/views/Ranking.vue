<template>
  <div class="ranking-page">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>🏆 基金排行</span>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-row :gutter="20" style="margin-bottom:20px">
        <el-col :span="6">
          <el-select v-model="fundType" placeholder="基金类型" style="width:100%" @change="fetchRanking">
            <el-option label="全部" value="全部" />
            <el-option label="股票型" value="股票型" />
            <el-option label="混合型" value="混合型" />
            <el-option label="债券型" value="债券型" />
            <el-option label="指数型" value="指数型" />
            <el-option label="QDII" value="QDII" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="sortBy" placeholder="排序方式" style="width:100%" @change="fetchRanking">
            <el-option label="近1年排名" value="rank_1y" />
            <el-option label="近3月排名" value="rank_3m" />
            <el-option label="近6月排名" value="rank_6m" />
            <el-option label="近3年排名" value="rank_3y" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="fetchRanking" :loading="loading" style="width:100%">查询</el-button>
        </el-col>
      </el-row>

      <!-- 排行表格 -->
      <el-table :data="rankingList" stripe highlight-current-row style="width:100%" v-loading="loading">
        <el-table-column type="index" label="序号" width="70" :index="(i) => (page - 1) * pageSize + i + 1" />
        <el-table-column prop="code" label="基金代码" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToDetail(row.code)">{{ row.code }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="rank_date" label="排名日期" width="120" />
        <el-table-column label="近3月排名" width="120" align="center">
          <template #default="{ row }">
            <span :class="getRankClass(row.rank_3m, row.total_count)">
              {{ row.rank_3m || '--' }}
            </span>
            <span v-if="row.total_count" class="rank-total">/{{ row.total_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="近6月排名" width="120" align="center">
          <template #default="{ row }">
            <span :class="getRankClass(row.rank_6m, row.total_count)">
              {{ row.rank_6m || '--' }}
            </span>
            <span v-if="row.total_count" class="rank-total">/{{ row.total_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="近1年排名" width="120" align="center">
          <template #default="{ row }">
            <span :class="getRankClass(row.rank_1y, row.total_count)">
              {{ row.rank_1y || '--' }}
            </span>
            <span v-if="row.total_count" class="rank-total">/{{ row.total_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="近3年排名" width="120" align="center">
          <template #default="{ row }">
            <span :class="getRankClass(row.rank_3y, row.total_count)">
              {{ row.rank_3y || '--' }}
            </span>
            <span v-if="row.total_count" class="rank-total">/{{ row.total_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToDetail(row.code)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div style="margin-top:20px;text-align:right">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchRanking"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFundRanking } from '../api/fund'

const router = useRouter()
const loading = ref(false)
const rankingList = ref([])
const fundType = ref('全部')
const sortBy = ref('rank_1y')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const getRankClass = (rank, totalCount) => {
  if (!rank || !totalCount) return ''
  const ratio = rank / totalCount
  if (ratio <= 0.1) return 'rank-top'
  if (ratio <= 0.3) return 'rank-good'
  return ''
}

const fetchRanking = async () => {
  loading.value = true
  try {
    const res = await getFundRanking(fundType.value, sortBy.value, page.value, pageSize)
    const data = res.data?.data || res.data || {}
    rankingList.value = data.items || data || []
    total.value = data.total || rankingList.value.length
  } catch (err) {
    console.error('获取排行失败:', err)
    ElMessage.error('获取排行数据失败')
    rankingList.value = []
  } finally {
    loading.value = false
  }
}

const goToDetail = (code) => {
  router.push(`/fund/${code}`)
}

onMounted(() => {
  fetchRanking()
})
</script>

<style scoped>
.ranking-page {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.main-card {
  margin-bottom: 20px;
}

.rank-top {
  color: #f56c6c;
  font-weight: 700;
  font-size: 15px;
}

.rank-good {
  color: #E6A23C;
  font-weight: 600;
}

.rank-total {
  color: #909399;
  font-size: 12px;
}
</style>
