<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <h1 @click="goHome">📊 基金分析器</h1>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

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
}

.el-main {
  min-height: calc(100vh - 60px);
  padding: 20px;
}
</style>
