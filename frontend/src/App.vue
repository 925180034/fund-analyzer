<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <h1 @click="goHome">📊 基金分析器</h1>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :ellipsis="false"
          class="header-menu"
          background-color="transparent"
          text-color="#ffffffcc"
          active-text-color="#ffffff"
          router
        >
          <el-menu-item index="/search">基金搜索</el-menu-item>
          <el-menu-item index="/ranking">基金排行</el-menu-item>
          <el-menu-item index="/backtest">定投回测</el-menu-item>
          <el-menu-item index="/portfolio">组合管理</el-menu-item>
          <el-menu-item index="/monitor">持仓监控</el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.path)

const goHome = () => {
  router.push('/search')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;
  background-color: #f5f7fa;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  height: 60px !important;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.app-header h1 {
  font-size: 22px;
  cursor: pointer;
  user-select: none;
  margin-right: 40px;
  white-space: nowrap;
}

.header-menu {
  flex: 1;
  border-bottom: none !important;
}

.header-menu .el-menu-item {
  border-bottom: none !important;
  font-size: 14px;
  height: 60px;
  line-height: 60px;
}

.header-menu .el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.15) !important;
}

.header-menu .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.2) !important;
  border-bottom: 2px solid #fff !important;
}

.el-main {
  min-height: calc(100vh - 60px);
  padding: 20px;
}
</style>
