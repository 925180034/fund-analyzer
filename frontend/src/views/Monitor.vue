<template>
  <div class="monitor-page">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>📋 持仓监控</span>
          <el-button type="primary" size="small" @click="showAddDialog = true">
            + 添加持仓
          </el-button>
        </div>
      </template>

      <!-- 风险提醒 -->
      <el-alert
        v-if="alerts.length > 0"
        v-for="(alert, idx) in alerts"
        :key="idx"
        :title="alert.title"
        :description="alert.message"
        :type="alert.type"
        show-icon
        closable
        style="margin-bottom:12px"
      />

      <!-- 持仓列表 -->
      <el-table :data="holdings" stripe highlight-current-row style="width:100%" v-if="holdings.length > 0">
        <el-table-column prop="fund_code" label="基金代码" width="120" />
        <el-table-column prop="fund_name" label="基金名称" min-width="180" />
        <el-table-column label="成本价" width="100">
          <template #default="{ row }">{{ row.cost_price || '--' }}</template>
        </el-table-column>
        <el-table-column label="最新净值" width="100">
          <template #default="{ row }">
            <span :class="(row.current_nav || 0) >= (row.cost_price || 0) ? 'price-up' : 'price-down'">
              {{ row.current_nav || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="持有份额" width="100">
          <template #default="{ row }">{{ row.shares || '--' }}</template>
        </el-table-column>
        <el-table-column label="市值" width="120">
          <template #default="{ row }">
            ¥{{ formatNum((row.current_nav || 0) * (row.shares || 0)) }}
          </template>
        </el-table-column>
        <el-table-column label="盈亏" width="120">
          <template #default="{ row }">
            <span :class="getProfit(row) >= 0 ? 'price-up' : 'price-down'">
              {{ getProfit(row) >= 0 ? '+' : '' }}¥{{ formatNum(getProfit(row)) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="收益率" width="100">
          <template #default="{ row }">
            <span :class="getProfitRate(row) >= 0 ? 'price-up' : 'price-down'">
              {{ getProfitRate(row) >= 0 ? '+' : '' }}{{ getProfitRate(row) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ $index }">
            <el-button type="danger" link @click="removeHolding($index)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="暂无持仓，点击右上角添加" />
    </el-card>

    <!-- 添加持仓对话框 -->
    <el-dialog v-model="showAddDialog" title="添加持仓" width="500px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="基金代码" required>
          <el-input v-model="addForm.fund_code" placeholder="请输入基金代码" @blur="lookupFund" />
        </el-form-item>
        <el-form-item label="基金名称">
          <el-input v-model="addForm.fund_name" placeholder="自动识别或手动输入" />
        </el-form-item>
        <el-form-item label="成本价" required>
          <el-input-number v-model="addForm.cost_price" :min="0" :step="0.0001" :precision="4" style="width:100%" />
        </el-form-item>
        <el-form-item label="持有份额" required>
          <el-input-number v-model="addForm.shares" :min="0" :step="100" style="width:100%" />
        </el-form-item>
        <el-form-item label="止损线(%)">
          <el-input-number v-model="addForm.stop_loss" :min="-50" :max="0" :step="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { searchFund } from '../api/fund'

const STORAGE_KEY = 'fund_monitor_holdings'
const holdings = ref([])
const showAddDialog = ref(false)

const addForm = ref({
  fund_code: '',
  fund_name: '',
  cost_price: 0,
  shares: 0,
  current_nav: null,
  stop_loss: -10
})

const formatNum = (num) => {
  if (num == null) return '--'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getProfit = (row) => {
  return ((row.current_nav || 0) - (row.cost_price || 0)) * (row.shares || 0)
}

const getProfitRate = (row) => {
  if (!row.cost_price || row.cost_price <= 0) return 0
  return (((row.current_nav || 0) - row.cost_price) / row.cost_price * 100).toFixed(2)
}

// 风险提醒
const alerts = computed(() => {
  const list = []
  holdings.value.forEach(h => {
    const rate = getProfitRate(h)
    if (h.stop_loss && Number(rate) <= h.stop_loss) {
      list.push({
        title: `${h.fund_name || h.fund_code} 触及止损线`,
        message: `当前收益率 ${rate}%，已触及止损线 ${h.stop_loss}%`,
        type: 'error'
      })
    } else if (Number(rate) <= -5) {
      list.push({
        title: `${h.fund_name || h.fund_code} 大幅亏损`,
        message: `当前收益率 ${rate}%，请注意风险`,
        type: 'warning'
      })
    }
  })
  return list
})

const loadHoldings = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    holdings.value = data ? JSON.parse(data) : []
    // 模拟刷新最新净值
    holdings.value.forEach(h => {
      if (!h.current_nav) {
        h.current_nav = h.cost_price * (1 + (Math.random() * 0.3 - 0.1))
        h.current_nav = Math.round(h.current_nav * 10000) / 10000
      }
    })
  } catch {
    holdings.value = []
  }
}

const saveHoldings = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings.value))
}

const lookupFund = async () => {
  if (!addForm.value.fund_code.trim()) return
  try {
    const res = await searchFund(addForm.value.fund_code)
    const funds = res.data?.data || res.data || []
    if (funds.length > 0) {
      addForm.value.fund_name = funds[0].name
      ElMessage.success(`已识别: ${funds[0].name}`)
    }
  } catch {
    // ignore
  }
}

const confirmAdd = () => {
  if (!addForm.value.fund_code.trim()) {
    ElMessage.warning('请输入基金代码')
    return
  }
  if (!addForm.value.cost_price || addForm.value.cost_price <= 0) {
    ElMessage.warning('请输入有效的成本价')
    return
  }
  if (!addForm.value.shares || addForm.value.shares <= 0) {
    ElMessage.warning('请输入有效的份额')
    return
  }

  // 模拟当前净值
  const currentNav = addForm.value.cost_price * (1 + (Math.random() * 0.3 - 0.1))
  holdings.value.push({
    ...addForm.value,
    current_nav: Math.round(currentNav * 10000) / 10000,
    added_at: new Date().toISOString()
  })
  saveHoldings()
  showAddDialog.value = false
  addForm.value = { fund_code: '', fund_name: '', cost_price: 0, shares: 0, current_nav: null, stop_loss: -10 }
  ElMessage.success('持仓添加成功')
}

const removeHolding = async (index) => {
  try {
    await ElMessageBox.confirm('确定移除该持仓？', '提示', { type: 'warning' })
    holdings.value.splice(index, 1)
    saveHoldings()
    ElMessage.success('已移除')
  } catch {}
}

onMounted(() => {
  loadHoldings()
})
</script>

<style scoped>
.monitor-page {
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

.price-up {
  color: #f56c6c;
  font-weight: 600;
}

.price-down {
  color: #67c23a;
  font-weight: 600;
}
</style>
