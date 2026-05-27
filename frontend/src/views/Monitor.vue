<template>
  <div class="page">
    <!-- 添加持仓按钮 -->
    <button class="ios-btn ios-btn-primary" @click="showAdd = true" style="margin-bottom: 16px">
      + 添加持仓
    </button>

    <!-- 风险提醒 -->
    <div v-if="alerts.length > 0" class="ios-card">
      <div class="ios-card-header">风险提醒</div>
      <div class="ios-card-body">
        <div v-for="alert in alerts" :key="alert.code + alert.type" class="alert-item" :class="alert.level">
          <div class="alert-icon">{{ alert.level === 'warning' ? '⚠️' : '📉' }}</div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.type }}</div>
            <div class="alert-desc">{{ alert.code }}: {{ alert.message }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="ios-loading">加载中...</div>

    <div v-else-if="holdings.length === 0" class="ios-empty">
      <div class="empty-icon">🔔</div>
      <div class="empty-text">暂无持仓</div>
    </div>

    <div v-else class="ios-list">
      <div v-for="h in holdings" :key="h.id" class="ios-list-item">
        <div class="item-content">
          <div class="item-title">{{ h.code }}</div>
          <div class="item-subtitle">
            买入价: {{ h.buy_price }} · 金额: {{ h.amount }}元
          </div>
        </div>
        <div class="item-right">
          <div class="profit" :class="h.profit >= 0 ? 'price-up' : 'price-down'">
            {{ h.profit >= 0 ? '+' : '' }}{{ h.profit }}%
          </div>
        </div>
      </div>
    </div>

    <!-- 添加持仓弹窗 -->
    <div v-if="showAdd" class="ios-modal" @click.self="showAdd = false">
      <div class="ios-modal-content">
        <div class="ios-modal-header">
          <span @click="showAdd = false">取消</span>
          <span class="modal-title">添加持仓</span>
          <span class="modal-save" @click="add">保存</span>
        </div>
        <div class="ios-modal-body">
          <div class="form-group">
            <label>基金代码</label>
            <input v-model="addForm.code" class="ios-input" placeholder="如 110011" />
          </div>
          <div class="form-group">
            <label>买入价格</label>
            <input v-model.number="addForm.buy_price" class="ios-input" type="number" step="0.0001" placeholder="3.5678" />
          </div>
          <div class="form-group">
            <label>买入日期</label>
            <input v-model="addForm.buy_date" class="ios-input" type="date" />
          </div>
          <div class="form-group">
            <label>买入金额 (元)</label>
            <input v-model.number="addForm.amount" class="ios-input" type="number" placeholder="10000" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHoldings, getAlerts, addHolding } from '../api/fund'

const holdings = ref([])
const alerts = ref([])
const loading = ref(false)
const showAdd = ref(false)

const addForm = ref({
  code: '',
  buy_price: 0,
  buy_date: '',
  amount: 10000
})

const loadData = async () => {
  loading.value = true
  try {
    const [holdingsRes, alertsRes] = await Promise.all([
      getHoldings(),
      getAlerts()
    ])
    holdings.value = holdingsRes.data?.holdings || []
    alerts.value = alertsRes.data?.alerts || []
  } catch (err) {
    console.error('加载失败:', err)
  } finally {
    loading.value = false
  }
}

const add = async () => {
  try {
    await addHolding(addForm.value)
    showAdd.value = false
    addForm.value = { code: '', buy_price: 0, buy_date: '', amount: 10000 }
    await loadData()
  } catch (err) {
    console.error('添加失败:', err)
  }
}

onMounted(loadData)
</script>

<style scoped>
.page {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 8px;
}

.alert-item.warning {
  background: rgba(255, 149, 0, 0.1);
}

.alert-item.danger {
  background: rgba(255, 59, 48, 0.1);
}

.alert-icon {
  font-size: 20px;
}

.alert-title {
  font-size: 15px;
  font-weight: 500;
}

.alert-desc {
  font-size: 13px;
  color: var(--ios-text3);
  margin-top: 2px;
}

.item-right {
  display: flex;
  align-items: center;
}

.profit {
  font-size: 17px;
  font-weight: 500;
}

/* iOS 弹窗 */
.ios-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.ios-modal-content {
  background: var(--ios-card);
  border-radius: var(--ios-radius-lg) var(--ios-radius-lg) 0 0;
  width: 100%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
}

.ios-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 0.5px solid var(--ios-gray5);
  position: sticky;
  top: 0;
  background: var(--ios-card);
}

.ios-modal-header span {
  font-size: 17px;
  color: var(--ios-blue);
  cursor: pointer;
}

.ios-modal-header .modal-title {
  font-weight: 600;
  color: var(--ios-text);
}

.ios-modal-header .modal-save {
  font-weight: 600;
}

.ios-modal-body {
  padding: 16px;
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
</style>
