<template>
  <el-container class="app-container">
    <el-aside width="200px">
      <div class="logo">恶意流量监控</div>
      <el-menu
        :default-active="activeMenu"
        router
        class="el-menu-vertical"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Warning /></el-icon>
          <span>告警列表</span>
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><PieChart /></el-icon>
          <span>统计分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-title">网络安全态势监控平台</div>
        <div class="header-status">
          <el-badge :is-dot="connected" class="status-item">
            <el-icon size="20"><Connection /></el-icon>
          </el-badge>
          <span class="status-text">{{ connected ? '已连接' : '未连接' }}</span>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Connection } from '@element-plus/icons-vue'
import { io } from 'socket.io-client'

const route = useRoute()
const socket = ref(null)
const connected = ref(false)

const activeMenu = computed(() => route.path)

onMounted(() => {
  socket.value = io('/', {
    transports: ['websocket', 'polling']
  })

  socket.value.on('connect', () => {
    connected.value = true
    socket.value.emit('request_stats')
  })

  socket.value.on('disconnect', () => {
    connected.value = false
  })
})

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect()
  }
})

defineExpose({ socket })
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
}

.app-container {
  height: 100%;
}

.el-aside {
  background-color: #304156;
  height: 100vh;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background-color: #2b3a4a;
}

.el-menu-vertical {
  border: none;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-title {
  font-size: 18px;
  font-weight: 500;
}

.header-status {
  display: flex;
  align-items: center;
}

.status-item {
  margin-right: 8px;
}

.status-text {
  font-size: 14px;
  color: #606266;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
