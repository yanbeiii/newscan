<template>
  <div class="alerts-page">
    <el-card>
      <template #header>
        <span>告警列表</span>
      </template>
      <el-form :inline="true" :model="filters" class="filters-form">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item label="源IP">
          <el-input v-model="filters.src_ip" placeholder="请输入源IP" clearable />
        </el-form-item>
        <el-form-item label="目的IP">
          <el-input v-model="filters.dst_ip" placeholder="请输入目的IP" clearable />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="filters.severity" placeholder="请选择" clearable>
            <el-option label="紧急" :value="1" />
            <el-option label="高" :value="2" />
            <el-option label="中" :value="3" />
            <el-option label="低" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="协议">
          <el-select v-model="filters.protocol" placeholder="请选择" clearable>
            <el-option label="TCP" value="TCP" />
            <el-option label="UDP" value="UDP" />
            <el-option label="ICMP" value="ICMP" />
            <el-option label="HTTP" value="HTTP" />
            <el-option label="HTTPS" value="HTTPS" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="alerts" style="width: 100%" v-loading="loading" @row-click="handleRowClick">
        <el-table-column prop="timestamp" label="时间" width="180" :formatter="formatTime"></el-table-column>
        <el-table-column prop="src_ip" label="源IP" width="140"></el-table-column>
        <el-table-column prop="src_port" label="源端口" width="100"></el-table-column>
        <el-table-column prop="dst_ip" label="目的IP" width="140"></el-table-column>
        <el-table-column prop="dst_port" label="目的端口" width="100"></el-table-column>
        <el-table-column prop="protocol" label="协议" width="80"></el-table-column>
        <el-table-column prop="severity" label="级别" width="80" :formatter="formatSeverity"></el-table-column>
        <el-table-column prop="signature" label="告警签名" min-width="200"></el-table-column>
        <el-table-column prop="action" label="动作" width="80"></el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; text-align: right"
      />
    </el-card>

    <el-dialog v-model="detailVisible" title="告警详情" width="700px">
      <el-descriptions :column="2" border v-if="currentAlert">
        <el-descriptions-item label="时间">{{ formatTime(currentAlert) }}</el-descriptions-item>
        <el-descriptions-item label="级别">{{ formatSeverity(currentAlert) }}</el-descriptions-item>
        <el-descriptions-item label="源IP">{{ currentAlert.src_ip }}</el-descriptions-item>
        <el-descriptions-item label="源端口">{{ currentAlert.src_port }}</el-descriptions-item>
        <el-descriptions-item label="目的IP">{{ currentAlert.dst_ip }}</el-descriptions-item>
        <el-descriptions-item label="目的端口">{{ currentAlert.dst_port }}</el-descriptions-item>
        <el-descriptions-item label="协议">{{ currentAlert.protocol }}</el-descriptions-item>
        <el-descriptions-item label="动作">{{ currentAlert.action }}</el-descriptions-item>
        <el-descriptions-item label="告警签名" :span="2">{{ currentAlert.signature }}</el-descriptions-item>
        <el-descriptions-item label="攻击分类" :span="2">{{ currentAlert.category }}</el-descriptions-item>
        <el-descriptions-item label="原始JSON" :span="2">
          <pre style="max-height: 200px; overflow: auto">{{ JSON.stringify(currentAlert.raw_json, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../utils/api'

const alerts = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const currentAlert = ref(null)
const dateRange = ref([])
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})
const filters = reactive({
  src_ip: '',
  dst_ip: '',
  severity: null,
  protocol: ''
})

const formatTime = (row) => {
  if (!row || !row.timestamp) return ''
  return new Date(row.timestamp).toLocaleString('zh-CN')
}

const formatSeverity = (row) => {
  if (!row) return ''
  const map = { 1: '紧急', 2: '高', 3: '中', 4: '低' }
  return map[row.severity] || '未知'
}

const handleDateChange = (val) => {
  if (val) {
    filters.start_time = val[0].toISOString()
    filters.end_time = val[1].toISOString()
  } else {
    filters.start_time = ''
    filters.end_time = ''
  }
}

const loadAlerts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filters
    }
    const data = await api.getAlerts(params)
    alerts.value = data.data || []
    pagination.total = data.total || 0
  } catch (error) {
    console.error('Failed to load alerts:', error)
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  pagination.page = 1
  loadAlerts()
}

const handleReset = () => {
  filters.src_ip = ''
  filters.dst_ip = ''
  filters.severity = null
  filters.protocol = ''
  dateRange.value = []
  filters.start_time = ''
  filters.end_time = ''
  handleQuery()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadAlerts()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  loadAlerts()
}

const handleRowClick = (row) => {
  currentAlert.value = row
  detailVisible.value = true
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alerts-page {
  height: 100%;
}

.filters-form {
  margin-bottom: 20px;
}
</style>
