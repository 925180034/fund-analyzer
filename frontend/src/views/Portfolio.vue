<template>
  <div class="portfolio-page">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>💼 组合管理</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true">
            + 创建组合
          </el-button>
        </div>
      </template>

      <el-table :data="portfolios" stripe highlight-current-row style="width:100%" v-if="portfolios.length > 0">
        <el-table-column prop="name" label="组合名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="基金数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.holdings?.length || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="120">
          <template #default="{ row }">
            {{ row.created_at?.substring(0, 10) || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row, $index }">
            <el-button type="primary" link @click="analyzePortfolio(row)">分析</el-button>
            <el-button type="success" link @click="addHolding($index)">添加基金</el-button>
            <el-button type="danger" link @click="deletePortfolio($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="暂无组合，点击右上角创建" />
    </el-card>

    <!-- 创建组合对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建组合" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="组合名称" required>
          <el-input v-model="createForm.name" placeholder="请输入组合名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入组合描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createPortfolio">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加基金对话框 -->
    <el-dialog v-model="showAddDialog" title="添加基金到组合" width="500px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="基金代码" required>
          <el-input v-model="addForm.fund_code" placeholder="请输入基金代码" />
        </el-form-item>
        <el-form-item label="权重(%)">
          <el-input-number v-model="addForm.weight" :min="0" :max="100" :step="5" style="width:100%" />
        </el-form-item>
        <el-form-item label="成本价">
          <el-input-number v-model="addForm.cost_price" :min="0" :step="0.01" :precision="4" style="width:100%" />
        </el-form-item>
        <el-form-item label="持有份额">
          <el-input-number v-model="addForm.shares" :min="0" :step="100" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddHolding">确定</el-button>
      </template>
    </el-dialog>

    <!-- 组合分析对话框 -->
    <el-dialog v-model="showAnalysisDialog" title="组合分析" width="700px">
      <div v-if="analysis">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="组合名称">{{ analysis.name }}</el-descriptions-item>
          <el-descriptions-item label="基金数量">{{ analysis.holdingCount }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>收益分析</el-divider>

        <el-row :gutter="20" style="margin-top:16px">
          <el-col :span="8">
            <div class="analysis-item">
              <div class="analysis-label">总投入</div>
              <div class="analysis-value">¥{{ formatNum(analysis.totalCost) }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="analysis-item">
              <div class="analysis-label">当前市值</div>
              <div class="analysis-value">¥{{ formatNum(analysis.currentValue) }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="analysis-item">
              <div class="analysis-label">总收益</div>
              <div class="analysis-value" :class="analysis.profit >= 0 ? 'price-up' : 'price-down'">
                {{ analysis.profit >= 0 ? '+' : '' }}¥{{ formatNum(analysis.profit) }}
              </div>
            </div>
          </el-col>
        </el-row>

        <el-divider>持仓明细</el-divider>
        <el-table :data="analysis.holdings" stripe size="small">
          <el-table-column prop="fund_code" label="基金代码" width="100" />
          <el-table-column label="权重" width="80">
            <template #default="{ row }">{{ row.weight }}%</template>
          </el-table-column>
          <el-table-column label="成本价" width="100">
            <template #default="{ row }">{{ row.cost_price || '--' }}</template>
          </el-table-column>
          <el-table-column label="份额" width="100">
            <template #default="{ row }">{{ row.shares || '--' }}</template>
          </el-table-column>
          <el-table-column label="成本" width="120">
            <template #default="{ row }">
              ¥{{ formatNum((row.cost_price || 0) * (row.shares || 0)) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const portfolios = ref([])
const showCreateDialog = ref(false)
const showAddDialog = ref(false)
const showAnalysisDialog = ref(false)
const analysis = ref(null)
const addIndex = ref(0)

const createForm = ref({ name: '', description: '' })
const addForm = ref({ fund_code: '', weight: 10, cost_price: 0, shares: 0 })

const STORAGE_KEY = 'fund_portfolios'

const formatNum = (num) => {
  if (num == null) return '--'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const loadPortfolios = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    portfolios.value = data ? JSON.parse(data) : []
  } catch {
    portfolios.value = []
  }
}

const savePortfolios = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(portfolios.value))
}

const createPortfolio = () => {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入组合名称')
    return
  }
  portfolios.value.push({
    name: createForm.value.name,
    description: createForm.value.description,
    holdings: [],
    created_at: new Date().toISOString()
  })
  savePortfolios()
  showCreateDialog.value = false
  createForm.value = { name: '', description: '' }
  ElMessage.success('组合创建成功')
}

const addHolding = (index) => {
  addIndex.value = index
  addForm.value = { fund_code: '', weight: 10, cost_price: 0, shares: 0 }
  showAddDialog.value = true
}

const confirmAddHolding = () => {
  if (!addForm.value.fund_code.trim()) {
    ElMessage.warning('请输入基金代码')
    return
  }
  portfolios.value[addIndex.value].holdings.push({ ...addForm.value })
  savePortfolios()
  showAddDialog.value = false
  ElMessage.success('基金添加成功')
}

const deletePortfolio = async (index) => {
  try {
    await ElMessageBox.confirm('确定删除该组合？', '提示', { type: 'warning' })
    portfolios.value.splice(index, 1)
    savePortfolios()
    ElMessage.success('已删除')
  } catch {}
}

const analyzePortfolio = (portfolio) => {
  let totalCost = 0
  portfolio.holdings.forEach(h => {
    totalCost += (h.cost_price || 0) * (h.shares || 0)
  })

  analysis.value = {
    name: portfolio.name,
    holdingCount: portfolio.holdings.length,
    totalCost,
    currentValue: totalCost * (1 + Math.random() * 0.2 - 0.05), // 模拟当前市值
    profit: 0,
    holdings: portfolio.holdings
  }
  analysis.value.profit = analysis.value.currentValue - analysis.value.totalCost
  showAnalysisDialog.value = true
}

onMounted(() => {
  loadPortfolios()
})
</script>

<style scoped>
.portfolio-page {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.main-card {
  margin-bottom: 20px;
}

.analysis-item {
  text-align: center;
  padding: 12px 0;
}

.analysis-label {
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
}

.analysis-value {
  font-size: 20px;
  font-weight: 600;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}
</style>
