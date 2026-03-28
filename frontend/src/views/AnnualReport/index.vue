<template>
  <div class="annual-report-page">
    <!-- 页面标题 -->
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">📊 年报分析</span>
      </template>
      <template #extra>
        <el-tag type="info">基于 PDF 财报深度解析</el-tag>
      </template>
    </el-page-header>

    <!-- 风险提示 -->
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      class="risk-alert"
    >
      <template #title>
        <strong>⚠️ 重要提示</strong>
      </template>
      本功能基于公开财报数据进行分析，结果仅供参考，不构成投资建议。请结合多方面信息独立判断。
    </el-alert>

    <!-- 主要内容区域 -->
    <el-row :gutter="24" class="main-content">
      <!-- 左侧：输入区域 -->
      <el-col :span="8">
        <el-card shadow="hover" class="input-card">
          <template #header>
            <div class="card-header">
              <el-icon><Upload /></el-icon>
              <span>数据输入</span>
            </div>
          </template>

          <!-- 方式选择 -->
          <el-radio-group v-model="inputMode" class="mode-selector">
            <el-radio-button label="search">🔍 搜索年报</el-radio-button>
            <el-radio-button label="upload">📤 上传文件</el-radio-button>
          </el-radio-group>

          <!-- 搜索模式 -->
          <div v-if="inputMode === 'search'" class="search-form">
            <el-form :model="searchForm" label-position="top">
              <el-form-item label="股票代码" required>
                <el-input
                  v-model="searchForm.symbol"
                  placeholder="输入6位股票代码，如 000026"
                  clearable
                  @keyup.enter="searchReports"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item label="报告类型">
                <el-select v-model="searchForm.reportType" style="width: 100%">
                  <el-option label="年度报告" value="annual" />
                  <el-option label="半年度报告" value="semi" />
                  <el-option label="第一季度报告" value="q1" />
                  <el-option label="第三季度报告" value="q3" />
                </el-select>
              </el-form-item>

              <el-form-item label="年份（可选）">
                <el-date-picker
                  v-model="searchForm.year"
                  type="year"
                  placeholder="选择年份"
                  format="YYYY"
                  value-format="YYYY"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  :loading="searching"
                  @click="searchReports"
                  style="width: 100%"
                >
                  <el-icon><Search /></el-icon>
                  搜索年报
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 搜索结果列表 -->
            <div v-if="searchResults.length > 0" class="search-results">
              <el-divider>搜索结果</el-divider>
              <el-scrollbar height="300px">
                <div
                  v-for="(report, index) in searchResults"
                  :key="index"
                  class="report-item"
                  :class="{ active: selectedReport === report }"
                  @click="selectReport(report)"
                >
                  <div class="report-title">{{ report.title }}</div>
                  <div class="report-meta">
                    <el-tag size="small" type="info">{{ report.announce_date }}</el-tag>
                    <el-tag size="small">{{ report.year }}年</el-tag>
                  </div>
                </div>
              </el-scrollbar>
            </div>
          </div>

          <!-- 上传模式 -->
          <div v-else class="upload-form">
            <el-upload
              ref="uploadRef"
              class="pdf-uploader"
              drag
              :auto-upload="false"
              :limit="1"
              accept=".pdf,.PDF"
              :on-change="handleFileChange"
              :on-exceed="handleExceed"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                拖拽 PDF 文件到此处，或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  仅支持 PDF 格式的财报文件，大小不超过 50MB
                </div>
              </template>
            </el-upload>

            <el-form :model="uploadForm" label-position="top" style="margin-top: 16px;">
              <el-form-item label="股票代码（可选）">
                <el-input
                  v-model="uploadForm.symbol"
                  placeholder="输入股票代码以便关联数据"
                />
              </el-form-item>
            </el-form>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button
              type="success"
              size="large"
              :loading="analyzing"
              :disabled="!canAnalyze"
              @click="startAnalysis"
              style="width: 100%"
            >
              <el-icon><DataAnalysis /></el-icon>
              开始分析
            </el-button>
          </div>
        </el-card>

        <!-- 历史记录 -->
        <el-card shadow="hover" class="history-card" v-if="analysisHistory.length > 0">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>分析历史</span>
            </div>
          </template>
          <el-scrollbar height="200px">
            <div
              v-for="item in analysisHistory"
              :key="item.id"
              class="history-item"
              @click="loadHistory(item)"
            >
              <div class="history-title">{{ item.title }}</div>
              <div class="history-time">{{ item.time }}</div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>

      <!-- 右侧：分析结果 -->
      <el-col :span="16">
        <el-card shadow="hover" class="result-card">
          <template #header>
            <div class="card-header">
              <div>
                <el-icon><Document /></el-icon>
                <span>分析结果</span>
              </div>
              <div v-if="analysisResult">
                <el-button type="primary" text @click="exportReport('markdown')">
                  <el-icon><Download /></el-icon> 导出 Markdown
                </el-button>
                <el-button type="primary" text @click="copyToClipboard">
                  <el-icon><CopyDocument /></el-icon> 复制
                </el-button>
              </div>
            </div>
          </template>

          <!-- 加载状态 -->
          <div v-if="analyzing" class="analyzing-container">
            <el-icon class="analyzing-icon"><Loading /></el-icon>
            <p>正在分析财报，请稍候...</p>
            <el-progress :percentage="analysisProgress" :stroke-width="10" />
          </div>

          <!-- 空状态 -->
          <el-empty
            v-else-if="!analysisResult"
            description="请搜索或上传年报 PDF 开始分析"
          >
            <template #image>
              <el-icon :size="80" color="#C0C4CC"><Document /></el-icon>
            </template>
          </el-empty>

          <!-- 分析结果 -->
          <div v-else class="analysis-result">
            <!-- 数据来源声明 -->
            <div class="source-declaration">
              <el-tag type="success" effect="plain">
                ✅ 数据来源：{{ analysisResult.source }}
              </el-tag>
              <span class="analysis-time">分析时间：{{ analysisResult.analysisTime }}</span>
            </div>

            <!-- 财务指标概览 -->
            <el-card shadow="never" class="metrics-overview">
              <template #header>
                <span>📊 关键财务指标</span>
              </template>
              <el-row :gutter="16">
                <el-col :span="6" v-for="metric in keyMetrics" :key="metric.name">
                  <div class="metric-card">
                    <div class="metric-value" :style="{ color: metric.color }">
                      {{ metric.value }}
                    </div>
                    <div class="metric-label">{{ metric.name }}</div>
                  </div>
                </el-col>
              </el-row>
            </el-card>

            <!-- 分析报告内容 -->
            <div class="report-content markdown-content" v-html="renderMarkdown(analysisResult.report)"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Upload,
  Search,
  DataAnalysis,
  Document,
  Download,
  CopyDocument,
  UploadFilled,
  Clock,
  Loading
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 配置 marked
marked.setOptions({ breaks: true, gfm: true })

// 状态
const inputMode = ref<'search' | 'upload'>('search')
const searching = ref(false)
const analyzing = ref(false)
const analysisProgress = ref(0)

// 搜索表单
const searchForm = ref({
  symbol: '',
  reportType: 'annual',
  year: ''
})

// 上传表单
const uploadForm = ref({
  symbol: ''
})

// 文件相关
const uploadRef = ref()
const uploadedFile = ref<File | null>(null)

// 搜索结果
const searchResults = ref<any[]>([])
const selectedReport = ref<any>(null)

// 分析结果
const analysisResult = ref<any>(null)

// 历史记录
const analysisHistory = ref<any[]>([])

// 关键指标
const keyMetrics = computed(() => {
  if (!analysisResult.value?.metrics) return []
  return analysisResult.value.metrics
})

// 是否可以分析
const canAnalyze = computed(() => {
  if (inputMode.value === 'search') {
    return selectedReport.value !== null
  } else {
    return uploadedFile.value !== null
  }
})

// 渲染 Markdown
const renderMarkdown = (content: string) => {
  if (!content) return ''
  try {
    return marked.parse(content) as string
  } catch (e) {
    return `<pre>${content}</pre>`
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 搜索年报
const searchReports = async () => {
  if (!searchForm.value.symbol) {
    ElMessage.warning('请输入股票代码')
    return
  }

  searching.value = true
  searchResults.value = []

  try {
    const response = await fetch(
      `/api/annual-report/search?symbol=${searchForm.value.symbol}&type=${searchForm.value.reportType}&year=${searchForm.value.year || ''}`,
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )

    const result = await response.json()
    if (result.success) {
      searchResults.value = result.data.reports || []
      if (searchResults.value.length === 0) {
        ElMessage.info('未找到匹配的年报')
      } else {
        ElMessage.success(`找到 ${searchResults.value.length} 份年报`)
      }
    } else {
      ElMessage.error(result.message || '搜索失败')
    }
  } catch (error: any) {
    console.error('搜索年报失败:', error)
    ElMessage.error('搜索失败，请检查网络连接')
  } finally {
    searching.value = false
  }
}

// 选择报告
const selectReport = (report: any) => {
  selectedReport.value = report
}

// 文件变化处理
const handleFileChange = (file: any) => {
  uploadedFile.value = file.raw
}

// 超出限制处理
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

// 开始分析
const startAnalysis = async () => {
  analyzing.value = true
  analysisProgress.value = 0
  analysisResult.value = null

  try {
    const formData = new FormData()

    if (inputMode.value === 'search' && selectedReport.value) {
      formData.append('pdf_url', selectedReport.value.pdf_url)
      formData.append('title', selectedReport.value.title)
      formData.append('symbol', searchForm.value.symbol)
    } else if (inputMode.value === 'upload' && uploadedFile.value) {
      formData.append('file', uploadedFile.value)
      formData.append('symbol', uploadForm.value.symbol)
    }

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (analysisProgress.value < 90) {
        analysisProgress.value += 10
      }
    }, 500)

    const response = await fetch('/api/annual-report/analyze', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      },
      body: formData
    })

    clearInterval(progressInterval)
    analysisProgress.value = 100

    const result = await response.json()
    if (result.success) {
      analysisResult.value = result.data

      // 添加到历史记录
      analysisHistory.value.unshift({
        id: Date.now(),
        title: result.data.title || '年报分析',
        time: new Date().toLocaleString(),
        result: result.data
      })

      // 只保留最近10条
      if (analysisHistory.value.length > 10) {
        analysisHistory.value = analysisHistory.value.slice(0, 10)
      }

      ElMessage.success('分析完成')
    } else {
      ElMessage.error(result.message || '分析失败')
    }
  } catch (error: any) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败，请重试')
  } finally {
    analyzing.value = false
  }
}

// 加载历史记录
const loadHistory = (item: any) => {
  analysisResult.value = item.result
}

// 导出报告
const exportReport = (format: string) => {
  if (!analysisResult.value) return

  const content = analysisResult.value.report
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `年报分析_${new Date().toISOString().slice(0, 10)}.md`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 复制到剪贴板
const copyToClipboard = async () => {
  if (!analysisResult.value) return

  try {
    await navigator.clipboard.writeText(analysisResult.value.report)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

onMounted(() => {
  // 可以从 localStorage 加载历史记录
})
</script>

<style lang="scss" scoped>
.annual-report-page {
  padding: 24px;

  .page-title {
    font-size: 20px;
    font-weight: 600;
  }

  .risk-alert {
    margin: 20px 0;
  }

  .main-content {
    margin-top: 20px;
  }

  .input-card,
  .history-card,
  .result-card {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-weight: 600;

    .el-icon {
      font-size: 18px;
    }
  }

  .mode-selector {
    width: 100%;
    margin-bottom: 20px;

    :deep(.el-radio-button__inner) {
      width: 100%;
    }
  }

  .search-results {
    .report-item {
      padding: 12px;
      margin-bottom: 8px;
      border: 1px solid var(--el-border-color-light);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        background-color: var(--el-fill-color-light);
      }

      &.active {
        border-color: var(--el-color-primary);
        background-color: var(--el-color-primary-light-9);
      }

      .report-title {
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 8px;
        line-height: 1.4;
      }

      .report-meta {
        display: flex;
        gap: 8px;
      }
    }
  }

  .pdf-uploader {
    :deep(.el-upload-dragger) {
      padding: 40px;
    }
  }

  .action-buttons {
    margin-top: 20px;
  }

  .history-card {
    .history-item {
      padding: 10px;
      margin-bottom: 8px;
      background-color: var(--el-fill-color-light);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        background-color: var(--el-fill-color);
      }

      .history-title {
        font-size: 14px;
        margin-bottom: 4px;
      }

      .history-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .analyzing-container {
    text-align: center;
    padding: 60px 0;

    .analyzing-icon {
      font-size: 60px;
      color: var(--el-color-primary);
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    p {
      margin: 20px 0;
      color: var(--el-text-color-secondary);
    }
  }

  .analysis-result {
    .source-declaration {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding: 12px 16px;
      background-color: var(--el-fill-color-light);
      border-radius: 8px;

      .analysis-time {
        font-size: 13px;
        color: var(--el-text-color-secondary);
      }
    }

    .metrics-overview {
      margin-bottom: 20px;

      .metric-card {
        text-align: center;
        padding: 16px;
        background-color: var(--el-fill-color-blank);
        border-radius: 8px;

        .metric-value {
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 8px;
        }

        .metric-label {
          font-size: 13px;
          color: var(--el-text-color-secondary);
        }
      }
    }

    .report-content {
      line-height: 1.8;

      :deep(h1), :deep(h2), :deep(h3) {
        margin: 24px 0 16px 0;
        color: var(--el-text-color-primary);
      }

      :deep(h1) { font-size: 22px; border-bottom: 1px solid var(--el-border-color); padding-bottom: 8px; }
      :deep(h2) { font-size: 18px; }
      :deep(h3) { font-size: 16px; }

      :deep(table) {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;

        th, td {
          border: 1px solid var(--el-border-color);
          padding: 10px 12px;
          text-align: left;
        }

        th {
          background-color: var(--el-fill-color-light);
          font-weight: 600;
        }
      }

      :deep(ul), :deep(ol) {
        padding-left: 24px;
        margin: 12px 0;
      }

      :deep(li) {
        margin: 6px 0;
      }

      :deep(blockquote) {
        margin: 16px 0;
        padding: 12px 16px;
        background-color: var(--el-fill-color-light);
        border-left: 4px solid var(--el-color-primary);
        color: var(--el-text-color-regular);
      }

      :deep(code) {
        background-color: var(--el-fill-color-light);
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
      }

      :deep(pre) {
        background-color: var(--el-fill-color-darker);
        padding: 16px;
        border-radius: 8px;
        overflow-x: auto;

        code {
          background: none;
          padding: 0;
        }
      }
    }
  }
}
</style>
