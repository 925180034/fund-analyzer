<template>
  <div class="app">
    <!-- iOS 风格导航栏 -->
    <header class="ios-nav">
      <div class="nav-content">
        <h1 class="nav-title">基金分析</h1>
      </div>
    </header>

    <!-- iOS 风格标签栏 -->
    <nav class="ios-tabbar">
      <router-link to="/search" class="tab-item" :class="{ active: $route.path === '/search' }">
        <span class="tab-icon">🔍</span>
        <span class="tab-label">搜索</span>
      </router-link>
      <router-link to="/ranking" class="tab-item" :class="{ active: $route.path === '/ranking' }">
        <span class="tab-icon">📊</span>
        <span class="tab-label">排行</span>
      </router-link>
      <router-link to="/backtest" class="tab-item" :class="{ active: $route.path === '/backtest' }">
        <span class="tab-icon">📈</span>
        <span class="tab-label">回测</span>
      </router-link>
      <router-link to="/portfolio" class="tab-item" :class="{ active: $route.path === '/portfolio' }">
        <span class="tab-icon">💼</span>
        <span class="tab-label">组合</span>
      </router-link>
      <router-link to="/monitor" class="tab-item" :class="{ active: $route.path === '/monitor' }">
        <span class="tab-icon">🔔</span>
        <span class="tab-label">监控</span>
      </router-link>
    </nav>

    <!-- 内容区域 -->
    <main class="content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
</script>

<style>
/* iOS 风格全局样式 */
:root {
  --ios-blue: #007AFF;
  --ios-green: #34C759;
  --ios-red: #FF3B30;
  --ios-orange: #FF9500;
  --ios-yellow: #FFCC00;
  --ios-purple: #AF52DE;
  --ios-pink: #FF2D55;
  --ios-teal: #5AC8FA;
  --ios-gray: #8E8E93;
  --ios-gray2: #AEAEB2;
  --ios-gray3: #C7C7CC;
  --ios-gray4: #D1D1D6;
  --ios-gray5: #E5E5EA;
  --ios-gray6: #F2F2F7;
  --ios-bg: #F2F2F7;
  --ios-card: #FFFFFF;
  --ios-text: #1C1C1E;
  --ios-text2: #3C3C43;
  --ios-text3: #8E8E93;
  --ios-radius: 12px;
  --ios-radius-lg: 16px;
  --ios-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', 'PingFang SC', sans-serif;
  background: var(--ios-bg);
  color: var(--ios-text);
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* iOS 导航栏 */
.ios-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(242, 242, 247, 0.85);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 0.5px solid rgba(0,0,0,0.1);
}

.nav-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-title {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.4px;
}

/* iOS 标签栏 */
.ios-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(249, 249, 249, 0.94);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-top: 0.5px solid rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-around;
  padding: 6px 0 env(safe-area-inset-bottom, 8px);
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 4px 12px;
  text-decoration: none;
  color: var(--ios-gray);
  transition: color 0.2s;
}

.tab-item.active {
  color: var(--ios-blue);
}

.tab-icon {
  font-size: 22px;
  line-height: 1;
}

.tab-label {
  font-size: 10px;
  font-weight: 500;
}

/* 内容区域 */
.content {
  flex: 1;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  padding: 8px 16px 80px;
}

/* iOS 卡片 */
.ios-card {
  background: var(--ios-card);
  border-radius: var(--ios-radius);
  box-shadow: var(--ios-shadow);
  overflow: hidden;
  margin-bottom: 12px;
}

.ios-card-header {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 400;
  color: var(--ios-text3);
  text-transform: uppercase;
  letter-spacing: -0.08px;
}

.ios-card-body {
  padding: 0 16px 12px;
}

/* iOS 列表 */
.ios-list {
  background: var(--ios-card);
  border-radius: var(--ios-radius);
  box-shadow: var(--ios-shadow);
  overflow: hidden;
  margin-bottom: 12px;
}

.ios-list-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 0.5px solid var(--ios-gray5);
  cursor: pointer;
  transition: background 0.15s;
}

.ios-list-item:last-child {
  border-bottom: none;
}

.ios-list-item:active {
  background: var(--ios-gray6);
}

.ios-list-item .item-content {
  flex: 1;
  min-width: 0;
}

.ios-list-item .item-title {
  font-size: 17px;
  color: var(--ios-text);
}

.ios-list-item .item-subtitle {
  font-size: 13px;
  color: var(--ios-text3);
  margin-top: 2px;
}

.ios-list-item .item-value {
  font-size: 17px;
  color: var(--ios-text2);
  margin-left: 8px;
}

.ios-list-item .item-arrow {
  color: var(--ios-gray3);
  margin-left: 4px;
  font-size: 14px;
}

/* iOS 按钮 */
.ios-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  border: none;
  border-radius: var(--ios-radius);
  font-size: 17px;
  font-weight: 400;
  cursor: pointer;
  transition: all 0.15s;
  width: 100%;
}

.ios-btn:active {
  transform: scale(0.98);
  opacity: 0.8;
}

.ios-btn-primary {
  background: var(--ios-blue);
  color: white;
}

.ios-btn-secondary {
  background: var(--ios-gray6);
  color: var(--ios-blue);
}

.ios-btn-danger {
  background: var(--ios-red);
  color: white;
}

/* iOS 输入框 */
.ios-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--ios-gray6);
  border: none;
  border-radius: var(--ios-radius);
  font-size: 17px;
  color: var(--ios-text);
  outline: none;
  transition: background 0.2s;
}

.ios-input:focus {
  background: var(--ios-gray5);
}

.ios-input::placeholder {
  color: var(--ios-gray2);
}

/* iOS 标签 */
.ios-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.ios-badge-blue {
  background: rgba(0, 122, 255, 0.12);
  color: var(--ios-blue);
}

.ios-badge-green {
  background: rgba(52, 199, 89, 0.12);
  color: var(--ios-green);
}

.ios-badge-red {
  background: rgba(255, 59, 48, 0.12);
  color: var(--ios-red);
}

.ios-badge-orange {
  background: rgba(255, 149, 0, 0.12);
  color: var(--ios-orange);
}

/* 价格颜色 */
.price-up {
  color: var(--ios-red);
}

.price-down {
  color: var(--ios-green);
}

/* iOS 搜索框 */
.ios-search {
  position: relative;
  margin-bottom: 16px;
}

.ios-search input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  background: var(--ios-gray6);
  border: none;
  border-radius: 10px;
  font-size: 17px;
  color: var(--ios-text);
  outline: none;
}

.ios-search .search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ios-gray);
  font-size: 16px;
}

/* iOS 分段控件 */
.ios-segment {
  display: flex;
  background: var(--ios-gray6);
  border-radius: 8px;
  padding: 2px;
  margin-bottom: 16px;
}

.ios-segment .segment-item {
  flex: 1;
  padding: 6px 12px;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: var(--ios-text2);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.ios-segment .segment-item.active {
  background: var(--ios-card);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  color: var(--ios-text);
}

/* iOS 统计数据 */
.ios-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.ios-stat-item {
  background: var(--ios-card);
  border-radius: var(--ios-radius);
  padding: 14px;
  box-shadow: var(--ios-shadow);
}

.ios-stat-label {
  font-size: 13px;
  color: var(--ios-text3);
  margin-bottom: 4px;
}

.ios-stat-value {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.5px;
}

/* iOS 空状态 */
.ios-empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--ios-text3);
}

.ios-empty .empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.ios-empty .empty-text {
  font-size: 17px;
}

/* iOS 加载 */
.ios-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: var(--ios-gray);
  font-size: 15px;
  gap: 8px;
}

.ios-loading::before {
  content: '';
  width: 20px;
  height: 20px;
  border: 2px solid var(--ios-gray4);
  border-top-color: var(--ios-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .content {
    padding: 8px 12px 80px;
  }
  
  .ios-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
