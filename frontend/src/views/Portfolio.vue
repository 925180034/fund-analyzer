<template>
  <div class="page">
    <!-- 创建组合按钮 -->
    <button class="ios-btn ios-btn-primary" @click="showCreate = true" style="margin-bottom: 16px">
      + 创建组合
    </button>

    <div v-if="loading" class="ios-loading">加载中...</div>

    <div v-else-if="portfolios.length === 0" class="ios-empty">
      <div class="empty-icon">💼</div>
      <div class="empty-text">暂无组合</div>
    </div>

    <div v-else>
      <div v-for="p in portfolios" :key="p.id" class="ios-card">
        <div class="portfolio-header">
          <div class="portfolio-name">{{ p.name }}</div>
          <div class="portfolio-desc">{{ p.description || '暂无描述' }}</div>
        </div>
        <div class="portfolio-holdings">
          <div v-for="h in p.holdings" :key="h.code" class="holding-tag">
            <span class="ios-badge ios-badge-blue">{{ h.code }}</span>
            <span class="weight">{{ (h.weight * 100).toFixed(0) }}%</span>
          </div>
        </div>
        <div class="portfolio-actions">
          <button class="ios-btn ios-btn-secondary" @click="analyze(p.id)">分析</button>
          <button class="ios-btn ios-btn-danger" @click="remove(p.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 创建组合弹窗 -->
    <div v-if="showCreate" class="ios-modal" @click.self="showCreate = false">
      <div class="ios-modal-content">
        <div class="ios-modal-header">
          <span @click="showCreate = false">取消</span>
          <span class="modal-title">创建组合</span>
          <span class="modal-save" @click="create">保存</span>
        </div>
        <div class="ios-modal-body">
          <div class="form-group">
            <label>组合名称</label>
            <input v-model="createForm.name" class="ios-input" placeholder="如：稳健组合" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="createForm.description" class="ios-input" placeholder="组合描述（可选）" />
          </div>
          <div class="form-group">
            <label>持仓基金</label>
            <div v-for="(h, i) in createForm.holdings" :key="i" class="holding-row">
              <input v-model="h.code" class="ios-input" placeholder="基金代码" />
              <input v-model.number="h.weight" class="ios-input" type="number" placeholder="权重" step="0.1" min="0" max="1" />
              <button class="remove-btn" @click="createForm.holdings.splice(i, 1)">×</button>
            </div>
            <button class="ios-btn ios-btn-secondary" @click="createForm.holdings.push({ code: '', weight: 0.2 })">
              + 添加基金
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分析结果弹窗 -->
    <div v-if="showAnalysis" class="ios-modal" @click.self="showAnalysis = false">
      <div class="ios-modal-content">
        <div class="ios-modal-header">
          <span @click="showAnalysis = false">关闭</span>
          <span class="modal-title">组合分析</span>
          <span></span>
        </div>
        <div class="ios-modal-body" v-if="analysis">
          <div class="ios-stats">
            <div class="ios-stat-item">
              <div class="ios-stat-label">总收益</div>
              <div class="ios-stat-value" :class="(analysis.total_return ?? 0) >= 0 ? 'price-up' : 'price-down'">
                {{ analysis.total_return }}%
              </div>
            </div>
            <div class="ios-stat-item">
              <div class="ios-stat-label">波动率</div>
              <div class="ios-stat-value">{{ analysis.volatility }}%</div>
            </div>
            <div class="ios-stat-item">
              <div class="ios-stat-label">最大回撤</div>
              <div class="ios-stat-value price-down">{{ analysis.max_drawdown }}%</div>
            </div>
            <div class="ios-stat-item">
              <div class="ios-stat-label">夏普比率</div>
              <div class="ios-stat-value">{{ analysis.sharpe }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPortfolioList, createPortfolio, deletePortfolio, analyzePortfolio } from '../api/fund'

const portfolios = ref([])
const loading = ref(false)
const showCreate = ref(false)
const showAnalysis = ref(false)
const analysis = ref(null)

const createForm = ref({
  name: '',
  description: '',
  holdings: [{ code: '', weight: 0.2 }]
})

const loadPortfolios = async () => {
  loading.value = true
  try {
    const res = await getPortfolioList()
    portfolios.value = res.data?.portfolios || []
  } catch (err) {
    console.error('获取组合失败:', err)
  } finally {
    loading.value = false
  }
}

const create = async () => {
  try {
    await createPortfolio(createForm.value)
    showCreate.value = false
    createForm.value = { name: '', description: '', holdings: [{ code: '', weight: 0.2 }] }
    await loadPortfolios()
  } catch (err) {
    console.error('创建失败:', err)
  }
}

const remove = async (id) => {
  try {
    await deletePortfolio(id)
    await loadPortfolios()
  } catch (err) {
    console.error('删除失败:', err)
  }
}

const analyze = async (id) => {
  try {
    const res = await analyzePortfolio(id)
    analysis.value = res.data?.analysis
    showAnalysis.value = true
  } catch (err) {
    console.error('分析失败:', err)
  }
}

onMounted(loadPortfolios)
</script>

<style scoped>
.page {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.portfolio-header {
  padding: 16px;
}

.portfolio-name {
  font-size: 18px;
  font-weight: 600;
}

.portfolio-desc {
  font-size: 13px;
  color: var(--ios-text3);
  margin-top: 4px;
}

.portfolio-holdings {
  padding: 0 16px 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.holding-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.weight {
  font-size: 13px;
  color: var(--ios-text3);
}

.portfolio-actions {
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  border-top: 0.5px solid var(--ios-gray5);
}

.portfolio-actions .ios-btn {
  flex: 1;
  padding: 8px;
  font-size: 15px;
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

.holding-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.holding-row .ios-input {
  flex: 1;
}

.remove-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--ios-red);
  color: white;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
