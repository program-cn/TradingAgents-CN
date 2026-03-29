<template>
  <div class="annual-report-page">
    <!-- 页面标题 -->
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">📊 年报分析</span>
      </template>
      <template #extra>
        <el-tag type="info">五维度财务指标 + 风险预警</el-tag>
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
        <strong>重要提示</strong>
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
            <el-radio-button label="search">搜索年报</el-radio-button>
            <el-radio-button label="upload">上传文件</el-radio-button>
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
                  <div class="report-title" v-html="report.title"></div>
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
              <div class="history-title">{{ item.name }}({{ item.symbol }})</div>
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
                  <el-icon><Download /></el-icon> 导出
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
              <div>
                <el-tag type="success" effect="plain">
                  数据来源：{{ analysisResult.source }}
                </el-tag>
                <el-tag type="info" effect="plain" style="margin-left: 8px;">
                  {{ analysisResult.symbol }} {{ analysisResult.name }}
                </el-tag>
              </div>
              <span class="analysis-time">{{ analysisResult.analysis_time }}</span>
            </div>

            <!-- 健康度评分 -->
            <el-card shadow="never" class="health-score-card">
              <div class="health-score-container">
                <div class="health-score-circle" :style="healthScoreStyle">
                  <span class="health-score-value">{{ analysisResult.health_score }}</span>
                </div>
                <div class="health-score-info">
                  <h3>财务健康度评分</h3>
                  <p :class="healthScoreClass">{{ healthScoreText }}</p>
                  <p class="health-desc">{{ healthScoreDesc }}</p>
                </div>
              </div>
            </el-card>

            <!-- PDF 提取的财务数据 -->
            <el-card shadow="never" class="financial-data-card" v-if="analysisResult.pdf_extracted && analysisResult.financial_data">
              <template #header>
                <div class="financial-header">
                  <span>财务报表数据（从 PDF 提取）</span>
                  <el-tag type="success" size="small">PDF 深度解析</el-tag>
                </div>
              </template>
              <el-row :gutter="24">
                <!-- 资产负债表 -->
                <el-col :span="8">
                  <h4>资产负债表</h4>
                  <el-descriptions :column="1" size="small" border>
                    <el-descriptions-item label="总资产">{{ formatLargeNumber(analysisResult.financial_data.total_assets) }}</el-descriptions-item>
                    <el-descriptions-item label="总负债">{{ formatLargeNumber(analysisResult.financial_data.total_liabilities) }}</el-descriptions-item>
                    <el-descriptions-item label="股东权益">{{ formatLargeNumber(analysisResult.financial_data.total_equity) }}</el-descriptions-item>
                    <el-descriptions-item label="流动资产">{{ formatLargeNumber(analysisResult.financial_data.current_assets) }}</el-descriptions-item>
                    <el-descriptions-item label="流动负债">{{ formatLargeNumber(analysisResult.financial_data.current_liabilities) }}</el-descriptions-item>
                    <el-descriptions-item label="货币资金">{{ formatLargeNumber(analysisResult.financial_data.cash) }}</el-descriptions-item>
                    <el-descriptions-item label="存货">{{ formatLargeNumber(analysisResult.financial_data.inventory) }}</el-descriptions-item>
                    <el-descriptions-item label="应收账款">{{ formatLargeNumber(analysisResult.financial_data.accounts_receivable) }}</el-descriptions-item>
                  </el-descriptions>
                </el-col>
                <!-- 利润表 -->
                <el-col :span="8">
                  <h4>利润表</h4>
                  <el-descriptions :column="1" size="small" border>
                    <el-descriptions-item label="营业收入">{{ formatLargeNumber(analysisResult.financial_data.revenue) }}</el-descriptions-item>
                    <el-descriptions-item label="营业成本">{{ formatLargeNumber(analysisResult.financial_data.operating_cost) }}</el-descriptions-item>
                    <el-descriptions-item label="毛利润">{{ formatLargeNumber(analysisResult.financial_data.gross_profit) }}</el-descriptions-item>
                    <el-descriptions-item label="营业利润">{{ formatLargeNumber(analysisResult.financial_data.operating_profit) }}</el-descriptions-item>
                    <el-descriptions-item label="净利润">{{ formatLargeNumber(analysisResult.financial_data.net_profit) }}</el-descriptions-item>
                    <el-descriptions-item label="归属净利润">{{ formatLargeNumber(analysisResult.financial_data.net_profit_attr) }}</el-descriptions-item>
                  </el-descriptions>
                </el-col>
                <!-- 现金流量表 -->
                <el-col :span="8">
                  <h4>现金流量表</h4>
                  <el-descriptions :column="1" size="small" border>
                    <el-descriptions-item label="经营现金流">{{ formatLargeNumber(analysisResult.financial_data.operating_cash_flow) }}</el-descriptions-item>
                    <el-descriptions-item label="投资现金流">{{ formatLargeNumber(analysisResult.financial_data.investing_cash_flow) }}</el-descriptions-item>
                    <el-descriptions-item label="筹资现金流">{{ formatLargeNumber(analysisResult.financial_data.financing_cash_flow) }}</el-descriptions-item>
                    <el-descriptions-item label="自由现金流">{{ formatLargeNumber(analysisResult.financial_data.free_cash_flow) }}</el-descriptions-item>
                  </el-descriptions>
                  <h4 style="margin-top: 16px;">每股指标</h4>
                  <el-descriptions :column="1" size="small" border>
                    <el-descriptions-item label="每股收益">{{ formatNumber(analysisResult.financial_data.eps) }} 元</el-descriptions-item>
                    <el-descriptions-item label="每股净资产">{{ formatNumber(analysisResult.financial_data.bvps) }} 元</el-descriptions-item>
                    <el-descriptions-item label="每股现金流">{{ formatNumber(analysisResult.financial_data.cfps) }} 元</el-descriptions-item>
                  </el-descriptions>
                </el-col>
              </el-row>
            </el-card>

            <!-- 关键指标概览 -->
            <el-card shadow="never" class="metrics-overview" v-if="keyMetrics.length > 0">
              <template #header>
                <span>核心财务指标</span>
              </template>
              <el-row :gutter="16">
                <el-col :span="6" v-for="metric in keyMetrics" :key="metric.name">
                  <div class="metric-card">
                    <div class="metric-value">{{ metric.value }}</div>
                    <div class="metric-label">{{ metric.name }}</div>
                  </div>
                </el-col>
              </el-row>
            </el-card>

            <!-- 风险信号 -->
            <el-card shadow="never" class="risk-signals-card" v-if="analysisResult.risk_signals?.length > 0">
              <template #header>
                <div class="risk-header">
                  <span>风险信号扫描</span>
                  <div class="risk-summary">
                    <el-tag type="danger" size="small">{{ highRiskCount }} 高风险</el-tag>
                    <el-tag type="warning" size="small">{{ midRiskCount }} 中风险</el-tag>
                    <el-tag type="success" size="small">{{ lowRiskCount }} 正常</el-tag>
                  </div>
                </div>
              </template>
              <el-table :data="analysisResult.risk_signals" style="width: 100%" size="small">
                <el-table-column prop="name" label="指标" width="140" />
                <el-table-column prop="value" label="当前值" width="100" />
                <el-table-column label="风险等级" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getRiskTagType(row.level)" size="small">
                      {{ row.level }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="说明" />
              </el-table>
            </el-card>

            <!-- 五维度财务指标分析卡片 -->
            <el-card shadow="never" class="five-dimension-card" v-if="hasFinancialMetrics">
              <template #header>
                <div class="five-dimension-header">
                  <span>五维度财务指标分析</span>
                  <el-tag type="primary" size="small">核心分析</el-tag>
                </div>
              </template>
              
              <!-- 一、每股指标 -->
              <div class="dimension-section" v-if="perShareMetrics.length > 0">
                <h4 class="dimension-title">
                  <span class="dimension-icon">📊</span>
                  一、每股指标
                  <span class="dimension-desc">反映每股股票的盈利和净资产情况</span>
                </h4>
                <el-row :gutter="16">
                  <el-col :span="6" v-for="item in perShareMetrics" :key="item.key">
                    <div class="metric-item" :class="item.status">
                      <div class="metric-name">{{ item.name }}</div>
                      <div class="metric-value">{{ item.value }}</div>
                      <div class="metric-analysis">{{ item.analysis }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
              
              <!-- 二、盈利能力 -->
              <div class="dimension-section" v-if="profitabilityMetrics.length > 0">
                <h4 class="dimension-title">
                  <span class="dimension-icon">💰</span>
                  二、盈利能力
                  <span class="dimension-desc">反映公司创造利润的能力</span>
                </h4>
                <el-row :gutter="16">
                  <el-col :span="6" v-for="item in profitabilityMetrics" :key="item.key">
                    <div class="metric-item" :class="item.status">
                      <div class="metric-name">{{ item.name }}</div>
                      <div class="metric-value">{{ item.value }}</div>
                      <div class="metric-analysis">{{ item.analysis }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
              
              <!-- 三、偿债能力 -->
              <div class="dimension-section" v-if="solvencyMetrics.length > 0">
                <h4 class="dimension-title">
                  <span class="dimension-icon">🏦</span>
                  三、偿债能力
                  <span class="dimension-desc">反映偿还债务的能力，财务安全的重要保障</span>
                </h4>
                <el-row :gutter="16">
                  <el-col :span="6" v-for="item in solvencyMetrics" :key="item.key">
                    <div class="metric-item" :class="item.status">
                      <div class="metric-name">{{ item.name }}</div>
                      <div class="metric-value">{{ item.value }}</div>
                      <div class="metric-analysis">{{ item.analysis }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
              
              <!-- 四、成长能力 -->
              <div class="dimension-section" v-if="growthMetrics.length > 0">
                <h4 class="dimension-title">
                  <span class="dimension-icon">📈</span>
                  四、成长能力
                  <span class="dimension-desc">反映业务扩张和盈利增长潜力</span>
                </h4>
                <el-row :gutter="16">
                  <el-col :span="6" v-for="item in growthMetrics" :key="item.key">
                    <div class="metric-item" :class="item.status">
                      <div class="metric-name">{{ item.name }}</div>
                      <div class="metric-value">{{ item.value }}</div>
                      <div class="metric-analysis">{{ item.analysis }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
              
              <!-- 五、运营能力 -->
              <div class="dimension-section" v-if="operationMetrics.length > 0">
                <h4 class="dimension-title">
                  <span class="dimension-icon">⚙️</span>
                  五、运营能力
                  <span class="dimension-desc">反映资产管理的效率，体现经营水平</span>
                </h4>
                <el-row :gutter="16">
                  <el-col :span="6" v-for="item in operationMetrics" :key="item.key">
                    <div class="metric-item" :class="item.status">
                      <div class="metric-name">{{ item.name }}</div>
                      <div class="metric-value">{{ item.value }}</div>
                      <div class="metric-analysis">{{ item.analysis }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
              
              <!-- 六、现金流质量 -->
              <div class="dimension-section" v-if="cashFlowMetrics.length > 0">
                <h4 class="dimension-title">
                  <span class="dimension-icon">💵</span>
                  六、现金流质量
                  <span class="dimension-desc">识别财务造假的核心指标，反映利润含金量</span>
                </h4>
                <el-row :gutter="16">
                  <el-col :span="6" v-for="item in cashFlowMetrics" :key="item.key">
                    <div class="metric-item" :class="item.status">
                      <div class="metric-name">{{ item.name }}</div>
                      <div class="metric-value">{{ item.value }}</div>
                      <div class="metric-analysis">{{ item.analysis }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </el-card>

            <!-- 财务指标详情（历史对比） -->
            <el-card shadow="never" class="metrics-detail-card" v-if="hasHistoricalMetrics">
              <template #header>
                <span>历史财务指标对比</span>
                <el-tag type="info" size="small" style="margin-left: 8px;">多期数据对比</el-tag>
              </template>
              <el-tabs v-model="activeMetricTab">
                <el-tab-pane label="每股指标" name="每股指标">
                  <el-table :data="getMetricsByCategory('每股指标')" size="small" v-if="getMetricsByCategory('每股指标').length > 0">
                    <el-table-column prop="name" label="指标" width="180" />
                    <el-table-column v-for="(period, idx) in analysisResult.periods" :key="idx" :label="period">
                      <template #default="{ row }">
                        {{ formatMetricValue(row.values[idx]) }}
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-empty v-else description="暂无每股指标数据" :image-size="60" />
                </el-tab-pane>
                <el-tab-pane label="盈利能力" name="盈利能力">
                  <el-table :data="getMetricsByCategory('盈利能力')" size="small" v-if="getMetricsByCategory('盈利能力').length > 0">
                    <el-table-column prop="name" label="指标" width="180" />
                    <el-table-column v-for="(period, idx) in analysisResult.periods" :key="idx" :label="period">
                      <template #default="{ row }">
                        {{ formatMetricValue(row.values[idx]) }}
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-empty v-else description="暂无盈利能力数据" :image-size="60" />
                </el-tab-pane>
                <el-tab-pane label="偿债能力" name="偿债能力">
                  <el-table :data="getMetricsByCategory('偿债能力')" size="small" v-if="getMetricsByCategory('偿债能力').length > 0">
                    <el-table-column prop="name" label="指标" width="180" />
                    <el-table-column v-for="(period, idx) in analysisResult.periods" :key="idx" :label="period">
                      <template #default="{ row }">
                        {{ formatMetricValue(row.values[idx]) }}
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-empty v-else description="暂无偿债能力数据" :image-size="60" />
                </el-tab-pane>
                <el-tab-pane label="成长能力" name="成长能力">
                  <el-table :data="getMetricsByCategory('成长能力')" size="small" v-if="getMetricsByCategory('成长能力').length > 0">
                    <el-table-column prop="name" label="指标" width="180" />
                    <el-table-column v-for="(period, idx) in analysisResult.periods" :key="idx" :label="period">
                      <template #default="{ row }">
                        {{ formatMetricValue(row.values[idx]) }}
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-empty v-else description="暂无成长能力数据" :image-size="60" />
                </el-tab-pane>
                <el-tab-pane label="运营能力" name="运营能力">
                  <el-table :data="getMetricsByCategory('运营能力')" size="small" v-if="getMetricsByCategory('运营能力').length > 0">
                    <el-table-column prop="name" label="指标" width="180" />
                    <el-table-column v-for="(period, idx) in analysisResult.periods" :key="idx" :label="period">
                      <template #default="{ row }">
                        {{ formatMetricValue(row.values[idx]) }}
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-empty v-else description="暂无运营能力数据" :image-size="60" />
                </el-tab-pane>
              </el-tabs>
            </el-card>

            <!-- 分析报告内容 -->
            <el-card shadow="never" class="report-content-card">
              <template #header>
                <span>详细分析报告</span>
              </template>
              <div class="report-content markdown-content" v-html="renderMarkdown(analysisResult.report)"></div>
            </el-card>
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
const activeMetricTab = ref('每股指标')

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

// 关键指标 - 从每股指标和盈利能力中提取
const keyMetrics = computed(() => {
  if (!analysisResult.value?.metrics) return []
  
  const metrics: any[] = []
  
  // EPS
  const eps = analysisResult.value.metrics['每股指标']?.['摊薄每股收益(元)']?.[0]
  if (eps) {
    metrics.push({ name: '每股收益(EPS)', value: eps + '元' })
  }
  
  // BPS
  const bps = analysisResult.value.metrics['每股指标']?.['每股净资产_调整后(元)']?.[0]
  if (bps) {
    metrics.push({ name: '每股净资产(BPS)', value: bps + '元' })
  }
  
  // ROE
  const roe = analysisResult.value.metrics['盈利能力']?.['净资产收益率(%)']?.[0]
  if (roe) {
    metrics.push({ name: 'ROE', value: roe + '%' })
  }
  
  // 毛利率
  const grossMargin = analysisResult.value.metrics['盈利能力']?.['销售毛利率(%)']?.[0]
  if (grossMargin) {
    metrics.push({ name: '毛利率', value: grossMargin + '%' })
  }
  
  return metrics.slice(0, 4)
})

// 健康度评分样式
const healthScoreStyle = computed(() => {
  const score = analysisResult.value?.health_score || 0
  let color = '#F56C6C'
  if (score >= 80) color = '#67C23A'
  else if (score >= 60) color = '#E6A23C'
  
  return {
    background: `conic-gradient(${color} ${score * 3.6}deg, #EBEEF5 0deg)`
  }
})

const healthScoreClass = computed(() => {
  const score = analysisResult.value?.health_score || 0
  if (score >= 80) return 'health-high'
  if (score >= 60) return 'health-medium'
  return 'health-low'
})

const healthScoreText = computed(() => {
  const score = analysisResult.value?.health_score || 0
  if (score >= 80) return '财务健康'
  if (score >= 60) return '财务一般'
  return '财务风险'
})

const healthScoreDesc = computed(() => {
  const score = analysisResult.value?.health_score || 0
  if (score >= 80) return '各项指标表现良好，财务状况稳健'
  if (score >= 60) return '部分指标需要关注，建议进一步分析'
  return '存在多项风险信号，需要重点关注'
})

// ==================== 五维度财务指标计算 ====================

// 一、每股指标
const perShareMetrics = computed(() => {
  const fd = analysisResult.value?.financial_data
  if (!fd) return []
  
  const metrics = []
  
  // EPS
  if (fd.eps != null) {
    let analysis = '盈利能力弱'
    let status = 'danger'
    if (fd.eps >= 1) { analysis = '盈利能力强'; status = 'success' }
    else if (fd.eps >= 0.3) { analysis = '盈利能力一般'; status = 'warning' }
    else if (fd.eps > 0) { analysis = '盈利能力较弱'; status = 'warning' }
    else { analysis = '每股亏损'; status = 'danger' }
    metrics.push({ key: 'eps', name: '每股收益(EPS)', value: fd.eps.toFixed(4) + ' 元', analysis, status })
  }
  
  // BPS
  if (fd.bvps != null) {
    let analysis = '净资产较低'
    let status = 'warning'
    if (fd.bvps >= 10) { analysis = '净资产雄厚'; status = 'success' }
    else if (fd.bvps >= 5) { analysis = '净资产一般'; status = 'normal' }
    metrics.push({ key: 'bvps', name: '每股净资产(BPS)', value: fd.bvps.toFixed(4) + ' 元', analysis, status })
  }
  
  // 每股经营现金流
  if (fd.cfps != null) {
    let analysis = fd.cfps > 0 ? '现金流良好' : '现金流需关注'
    let status = fd.cfps > 0 ? 'success' : 'warning'
    metrics.push({ key: 'cfps', name: '每股经营现金流', value: fd.cfps.toFixed(4) + ' 元', analysis, status })
  }
  
  // 每股未分配利润
  if (fd.retained_eps != null) {
    metrics.push({ key: 'retained_eps', name: '每股未分配利润', value: fd.retained_eps.toFixed(4) + ' 元', analysis: '-', status: 'normal' })
  }
  
  return metrics
})

// 二、盈利能力指标
const profitabilityMetrics = computed(() => {
  const fd = analysisResult.value?.financial_data
  if (!fd) return []
  
  const metrics = []
  
  // ROE
  if (fd.roe != null) {
    let analysis = '较弱'
    let status = 'danger'
    if (fd.roe >= 20) { analysis = '优秀'; status = 'success' }
    else if (fd.roe >= 15) { analysis = '良好'; status = 'success' }
    else if (fd.roe >= 8) { analysis = '一般'; status = 'warning' }
    metrics.push({ key: 'roe', name: 'ROE净资产收益率', value: fd.roe.toFixed(2) + '%', analysis, status })
  }
  
  // ROA
  if (fd.roa != null) {
    let analysis = '较弱'
    let status = 'danger'
    if (fd.roa >= 10) { analysis = '优秀'; status = 'success' }
    else if (fd.roa >= 5) { analysis = '良好'; status = 'normal' }
    else if (fd.roa >= 2) { analysis = '一般'; status = 'warning' }
    metrics.push({ key: 'roa', name: 'ROA总资产收益率', value: fd.roa.toFixed(2) + '%', analysis, status })
  }
  
  // 毛利率
  if (fd.gross_margin != null) {
    let analysis = '竞争力弱'
    let status = 'danger'
    if (fd.gross_margin >= 50) { analysis = '竞争力强'; status = 'success' }
    else if (fd.gross_margin >= 30) { analysis = '竞争力良好'; status = 'success' }
    else if (fd.gross_margin >= 15) { analysis = '竞争力一般'; status = 'warning' }
    metrics.push({ key: 'gross_margin', name: '销售毛利率', value: fd.gross_margin.toFixed(2) + '%', analysis, status })
  }
  
  // 净利率
  if (fd.net_margin != null) {
    let analysis = '盈利质量差'
    let status = 'danger'
    if (fd.net_margin >= 15) { analysis = '盈利质量优秀'; status = 'success' }
    else if (fd.net_margin >= 8) { analysis = '盈利质量良好'; status = 'success' }
    else if (fd.net_margin >= 3) { analysis = '盈利质量一般'; status = 'warning' }
    metrics.push({ key: 'net_margin', name: '销售净利率', value: fd.net_margin.toFixed(2) + '%', analysis, status })
  }
  
  // 营业利润率
  if (fd.operating_margin != null) {
    let analysis = fd.operating_margin >= 15 ? '主业盈利强' : (fd.operating_margin >= 5 ? '主业盈利一般' : '主业盈利弱')
    let status = fd.operating_margin >= 15 ? 'success' : (fd.operating_margin >= 5 ? 'warning' : 'danger')
    metrics.push({ key: 'operating_margin', name: '营业利润率', value: fd.operating_margin.toFixed(2) + '%', analysis, status })
  }
  
  return metrics
})

// 三、偿债能力指标
const solvencyMetrics = computed(() => {
  const fd = analysisResult.value?.financial_data
  if (!fd) return []
  
  const metrics = []
  
  // 资产负债率
  if (fd.debt_ratio != null) {
    let analysis = '高风险'
    let status = 'danger'
    if (fd.debt_ratio <= 40) { analysis = '非常稳健'; status = 'success' }
    else if (fd.debt_ratio <= 60) { analysis = '稳健'; status = 'success' }
    else if (fd.debt_ratio <= 70) { analysis = '需关注'; status = 'warning' }
    metrics.push({ key: 'debt_ratio', name: '资产负债率', value: fd.debt_ratio.toFixed(2) + '%', analysis, status })
  }
  
  // 流动比率
  if (fd.current_ratio != null) {
    let analysis = '压力大'
    let status = 'danger'
    if (fd.current_ratio >= 2) { analysis = '优秀'; status = 'success' }
    else if (fd.current_ratio >= 1.5) { analysis = '良好'; status = 'success' }
    else if (fd.current_ratio >= 1) { analysis = '尚可'; status = 'warning' }
    metrics.push({ key: 'current_ratio', name: '流动比率', value: fd.current_ratio.toFixed(2), analysis, status })
  }
  
  // 速动比率
  if (fd.quick_ratio != null) {
    let analysis = fd.quick_ratio >= 1 ? '充足' : '需警惕'
    let status = fd.quick_ratio >= 1 ? 'success' : 'warning'
    if (fd.quick_ratio >= 1.5) { analysis = '非常充足'; status = 'success' }
    metrics.push({ key: 'quick_ratio', name: '速动比率', value: fd.quick_ratio.toFixed(2), analysis, status })
  }
  
  // 利息保障倍数
  if (fd.interest_coverage != null) {
    let analysis = '压力大'
    let status = 'danger'
    let displayValue = fd.interest_coverage.toFixed(2) + '倍'
    
    if (fd.interest_coverage >= 100) {
      // 特殊值：表示几乎没有有息负债
      analysis = '无有息负债'
      status = 'success'
      displayValue = '极高（无有息负债）'
    } else if (fd.interest_coverage >= 5) { 
      analysis = '很强'; 
      status = 'success' 
    } else if (fd.interest_coverage >= 3) { 
      analysis = '尚可'; 
      status = 'warning' 
    } else if (fd.interest_coverage >= 1) { 
      analysis = '压力较大'; 
      status = 'danger' 
    }
    
    metrics.push({ key: 'interest_coverage', name: '利息保障倍数', value: displayValue, analysis, status })
  }
  
  return metrics
})

// 四、成长能力指标
const growthMetrics = computed(() => {
  const fd = analysisResult.value?.financial_data
  if (!fd) return []
  
  const metrics = []
  
  // 营收增长率
  if (fd.revenue_growth != null) {
    let analysis = '收缩'
    let status = 'danger'
    if (fd.revenue_growth >= 30) { analysis = '高增长'; status = 'success' }
    else if (fd.revenue_growth >= 10) { analysis = '稳定增长'; status = 'success' }
    else if (fd.revenue_growth >= 0) { analysis = '增长放缓'; status = 'warning' }
    metrics.push({ key: 'revenue_growth', name: '营业收入增长率', value: fd.revenue_growth.toFixed(2) + '%', analysis, status })
  }
  
  // 净利润增长率
  if (fd.net_profit_growth != null) {
    let analysis = '下滑'
    let status = 'danger'
    if (fd.net_profit_growth >= 30) { analysis = '高增长'; status = 'success' }
    else if (fd.net_profit_growth >= 10) { analysis = '稳定增长'; status = 'success' }
    else if (fd.net_profit_growth >= 0) { analysis = '增长放缓'; status = 'warning' }
    metrics.push({ key: 'net_profit_growth', name: '净利润增长率', value: fd.net_profit_growth.toFixed(2) + '%', analysis, status })
  }
  
  // 总资产增长率
  if (fd.total_assets_growth != null) {
    let analysis = fd.total_assets_growth >= 10 ? '扩张快' : (fd.total_assets_growth >= 0 ? '稳定' : '收缩')
    let status = fd.total_assets_growth >= 10 ? 'success' : (fd.total_assets_growth >= 0 ? 'normal' : 'danger')
    metrics.push({ key: 'total_assets_growth', name: '总资产增长率', value: fd.total_assets_growth.toFixed(2) + '%', analysis, status })
  }
  
  // 净资产增长率
  if (fd.net_assets_growth != null) {
    let analysis = fd.net_assets_growth >= 0 ? '增长' : '下降'
    let status = fd.net_assets_growth >= 0 ? 'success' : 'warning'
    metrics.push({ key: 'net_assets_growth', name: '净资产增长率', value: fd.net_assets_growth.toFixed(2) + '%', analysis, status })
  }
  
  return metrics
})

// 五、运营能力指标
const operationMetrics = computed(() => {
  const fd = analysisResult.value?.financial_data
  if (!fd) return []
  
  const metrics = []
  
  // 存货周转率
  if (fd.inventory_turnover != null) {
    let analysis = '积压风险'
    let status = 'danger'
    if (fd.inventory_turnover >= 6) { analysis = '效率高'; status = 'success' }
    else if (fd.inventory_turnover >= 3) { analysis = '效率一般'; status = 'warning' }
    metrics.push({ key: 'inventory_turnover', name: '存货周转率', value: fd.inventory_turnover.toFixed(2) + '次', analysis, status })
  }
  
  // 存货周转天数
  if (fd.inventory_turnover_days != null) {
    let analysis = fd.inventory_turnover_days <= 60 ? '良好' : (fd.inventory_turnover_days <= 120 ? '一般' : '较慢')
    let status = fd.inventory_turnover_days <= 60 ? 'success' : (fd.inventory_turnover_days <= 120 ? 'warning' : 'danger')
    metrics.push({ key: 'inventory_turnover_days', name: '存货周转天数', value: fd.inventory_turnover_days.toFixed(0) + '天', analysis, status })
  }
  
  // 应收账款周转率
  if (fd.accounts_receivable_turnover != null) {
    let analysis = '回款风险'
    let status = 'danger'
    if (fd.accounts_receivable_turnover >= 10) { analysis = '回款强'; status = 'success' }
    else if (fd.accounts_receivable_turnover >= 5) { analysis = '回款一般'; status = 'warning' }
    metrics.push({ key: 'accounts_receivable_turnover', name: '应收账款周转率', value: fd.accounts_receivable_turnover.toFixed(2) + '次', analysis, status })
  }
  
  // 总资产周转率
  if (fd.total_assets_turnover != null) {
    let analysis = '效率低'
    let status = 'danger'
    if (fd.total_assets_turnover >= 1) { analysis = '效率高'; status = 'success' }
    else if (fd.total_assets_turnover >= 0.5) { analysis = '效率一般'; status = 'warning' }
    metrics.push({ key: 'total_assets_turnover', name: '总资产周转率', value: fd.total_assets_turnover.toFixed(2) + '次', analysis, status })
  }
  
  // 营业周期
  if (fd.operating_cycle != null) {
    let analysis = '周转慢'
    let status = 'danger'
    if (fd.operating_cycle <= 60) { analysis = '周转快'; status = 'success' }
    else if (fd.operating_cycle <= 120) { analysis = '周转一般'; status = 'warning' }
    metrics.push({ key: 'operating_cycle', name: '营业周期', value: fd.operating_cycle.toFixed(0) + '天', analysis, status })
  }
  
  return metrics
})

// 六、现金流质量指标
const cashFlowMetrics = computed(() => {
  const fd = analysisResult.value?.financial_data
  if (!fd) return []
  
  const metrics = []
  
  // 净现比
  if (fd.net_cash_ratio != null) {
    let analysis = '预警'
    let status = 'danger'
    if (fd.net_cash_ratio >= 1.2) { analysis = '质量高'; status = 'success' }
    else if (fd.net_cash_ratio >= 1) { analysis = '质量良好'; status = 'success' }
    else if (fd.net_cash_ratio >= 0.7) { analysis = '需关注'; status = 'warning' }
    else { analysis = '⚠️预警'; status = 'danger' }
    metrics.push({ key: 'net_cash_ratio', name: '净现比', value: fd.net_cash_ratio.toFixed(2), analysis, status })
  }
  
  // 销售现金比率
  if (fd.cash_to_sales != null) {
    let analysis = fd.cash_to_sales >= 1 ? '回款正常' : '应收款多'
    let status = fd.cash_to_sales >= 1 ? 'success' : 'warning'
    if (fd.cash_to_sales >= 1.1) { analysis = '回款好'; status = 'success' }
    metrics.push({ key: 'cash_to_sales', name: '销售现金比率', value: fd.cash_to_sales.toFixed(2), analysis, status })
  }
  
  // 经营现金流
  if (fd.operating_cash_flow != null) {
    let analysis = fd.operating_cash_flow > 0 ? '正向' : '负向'
    let status = fd.operating_cash_flow > 0 ? 'success' : 'danger'
    metrics.push({ key: 'operating_cash_flow', name: '经营现金流', value: formatLargeNumber(fd.operating_cash_flow), analysis, status })
  }
  
  // 自由现金流
  if (fd.free_cash_flow != null) {
    let analysis = fd.free_cash_flow > 0 ? '正向' : '负向'
    let status = fd.free_cash_flow > 0 ? 'success' : 'warning'
    metrics.push({ key: 'free_cash_flow', name: '自由现金流', value: formatLargeNumber(fd.free_cash_flow), analysis, status })
  }
  
  return metrics
})

// 是否有五维度财务指标数据（用于条件显示）
const hasFinancialMetrics = computed(() => {
  return perShareMetrics.value.length > 0 ||
         profitabilityMetrics.value.length > 0 ||
         solvencyMetrics.value.length > 0 ||
         growthMetrics.value.length > 0 ||
         operationMetrics.value.length > 0 ||
         cashFlowMetrics.value.length > 0
})

// 是否有历史指标数据（用于条件显示）
const hasHistoricalMetrics = computed(() => {
  if (!analysisResult.value?.periods?.length) return false
  if (!analysisResult.value?.metrics) return false
  
  // 检查是否有任何一个类别有数据
  const categories = ['每股指标', '盈利能力', '偿债能力', '成长能力', '运营能力']
  return categories.some(cat => {
    const catMetrics = analysisResult.value?.metrics?.[cat] || {}
    return Object.keys(catMetrics).length > 0
  })
})

// 风险统计
const highRiskCount = computed(() => {
  return analysisResult.value?.risk_signals?.filter((r: any) => r.level === '高').length || 0
})

const midRiskCount = computed(() => {
  return analysisResult.value?.risk_signals?.filter((r: any) => r.level === '中').length || 0
})

const lowRiskCount = computed(() => {
  return analysisResult.value?.risk_signals?.filter((r: any) => r.level === '低').length || 0
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

// 获取风险标签类型
const getRiskTagType = (level: string) => {
  if (level === '高') return 'danger'
  if (level === '中') return 'warning'
  return 'success'
}

// 按类别获取指标
const getMetricsByCategory = (category: string) => {
  const metrics = analysisResult.value?.metrics?.[category] || {}
  return Object.entries(metrics).map(([name, values]) => ({
    name,
    values: values as (string | null)[]
  }))
}

// 格式化指标值
const formatMetricValue = (value: string | null) => {
  if (value === null || value === undefined) return 'N/A'
  return value
}

// 格式化大数字（转换为亿/万单位）
const formatLargeNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'N/A'
  const absVal = Math.abs(value)
  const sign = value < 0 ? '-' : ''
  
  if (absVal >= 1e12) {
    return `${sign}${(absVal / 1e12).toFixed(2)}万亿`
  } else if (absVal >= 1e8) {
    return `${sign}${(absVal / 1e8).toFixed(2)}亿`
  } else if (absVal >= 1e4) {
    return `${sign}${(absVal / 1e4).toFixed(2)}万`
  } else {
    return `${sign}${absVal.toFixed(2)}`
  }
}

// 格式化普通数字
const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'N/A'
  return value.toFixed(4)
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
        name: result.data.name,
        symbol: result.data.symbol,
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
  a.download = `年报分析_${analysisResult.value.symbol}_${new Date().toISOString().slice(0, 10)}.md`
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

    .health-score-card {
      margin-bottom: 20px;

      .health-score-container {
        display: flex;
        align-items: center;
        gap: 32px;

        .health-score-circle {
          width: 120px;
          height: 120px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;

          &::before {
            content: '';
            position: absolute;
            width: 90px;
            height: 90px;
            background: var(--el-bg-color);
            border-radius: 50%;
          }

          .health-score-value {
            position: relative;
            font-size: 32px;
            font-weight: 700;
            z-index: 1;
          }
        }

        .health-score-info {
          h3 {
            font-size: 18px;
            margin: 0 0 8px 0;
          }

          p {
            margin: 4px 0;
            font-size: 14px;
          }

          .health-high { color: #67C23A; font-weight: 600; }
          .health-medium { color: #E6A23C; font-weight: 600; }
          .health-low { color: #F56C6C; font-weight: 600; }

          .health-desc {
            color: var(--el-text-color-secondary);
          }
        }
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
          color: var(--el-color-primary);
        }

        .metric-label {
          font-size: 13px;
          color: var(--el-text-color-secondary);
        }
      }
    }

    .financial-data-card {
      margin-bottom: 20px;

      .financial-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        color: var(--el-text-color-primary);
        font-weight: 600;
      }

      :deep(.el-descriptions__label) {
        width: 80px;
        font-size: 12px;
      }

      :deep(.el-descriptions__content) {
        font-size: 12px;
        font-family: 'Consolas', 'Monaco', monospace;
      }
    }

    .risk-signals-card {
      margin-bottom: 20px;

      .risk-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .risk-summary {
          display: flex;
          gap: 8px;
        }
      }
    }

    .five-dimension-card {
      margin-bottom: 20px;

      .five-dimension-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .dimension-section {
        margin-bottom: 24px;
        padding-bottom: 20px;
        border-bottom: 1px dashed var(--el-border-color-lighter);

        &:last-child {
          margin-bottom: 0;
          padding-bottom: 0;
          border-bottom: none;
        }
      }

      .dimension-title {
        margin: 0 0 16px 0;
        font-size: 15px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        display: flex;
        align-items: center;
        gap: 8px;

        .dimension-icon {
          font-size: 18px;
        }

        .dimension-desc {
          font-size: 12px;
          font-weight: 400;
          color: var(--el-text-color-secondary);
          margin-left: 8px;
        }
      }

      .metric-item {
        padding: 16px;
        border-radius: 8px;
        background-color: var(--el-fill-color-blank);
        border: 1px solid var(--el-border-color-lighter);
        text-align: center;
        transition: all 0.3s;

        &:hover {
          border-color: var(--el-color-primary-light-5);
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
        }

        &.success {
          border-left: 3px solid #67C23A;
          .metric-value { color: #67C23A; }
        }

        &.warning {
          border-left: 3px solid #E6A23C;
          .metric-value { color: #E6A23C; }
        }

        &.danger {
          border-left: 3px solid #F56C6C;
          .metric-value { color: #F56C6C; }
        }

        &.normal {
          border-left: 3px solid var(--el-color-primary);
          .metric-value { color: var(--el-color-primary); }
        }

        .metric-name {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          margin-bottom: 8px;
        }

        .metric-value {
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 6px;
        }

        .metric-analysis {
          font-size: 11px;
          color: var(--el-text-color-regular);
          padding: 2px 8px;
          background-color: var(--el-fill-color-light);
          border-radius: 10px;
          display: inline-block;
        }
      }
    }

    .metrics-detail-card {
      margin-bottom: 20px;
    }

    .report-content-card {
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
}
</style>
