<template>
  <div class="market-overview">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><TrendCharts /></el-icon>
        市场概览
      </h1>
      <p class="page-description">
        财联社实时新闻 · 资金流排行榜
      </p>
    </div>

    <!-- 操作栏 -->
    <el-card class="action-card" shadow="never">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-select v-model="hoursBack" placeholder="时间范围" @change="refreshData">
            <el-option label="最近 6 小时" :value="6" />
            <el-option label="最近 12 小时" :value="12" />
            <el-option label="最近 24 小时" :value="24" />
            <el-option label="最近 48 小时" :value="48" />
            <el-option label="最近 72 小时" :value="72" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="newsLimit" placeholder="新闻数量" @change="refreshData">
            <el-option label="20 条" :value="20" />
            <el-option label="30 条" :value="30" />
            <el-option label="50 条" :value="50" />
            <el-option label="100 条" :value="100" />
          </el-select>
        </el-col>
        <el-col :span="12" style="text-align: right;">
          <el-button @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <span class="update-time" v-if="updateTime">
            更新时间: {{ formatTime(updateTime) }}
          </span>
        </el-col>
      </el-row>
    </el-card>

    <!-- 主内容区 -->
    <el-row :gutter="24" class="main-content">
      <!-- 左侧：新闻列表 -->
      <el-col :span="16">
        <el-card class="news-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Document /></el-icon>
                实时新闻
                <el-tag size="small" type="info" style="margin-left: 8px;">
                  来源: 财联社
                </el-tag>
              </span>
              <span class="news-count">
                共 {{ newsList.length }} 条
              </span>
            </div>
          </template>

          <div v-loading="loading" class="news-list">
            <template v-if="newsList.length > 0">
              <div
                v-for="(news, index) in newsList"
                :key="news.hash || index"
                class="news-item"
              >
                <div class="news-time">
                  {{ formatNewsTime(news.datetime) }}
                </div>
                <div class="news-content">
                  <div class="news-title">{{ news.title }}</div>
                  <div class="news-text">{{ news.content }}</div>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无新闻数据" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：资金流排行 -->
      <el-col :span="8">
        <!-- 行业资金流 -->
        <el-card class="fund-flow-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Coin /></el-icon>
                行业资金流
                <el-tag size="small" :type="flowType === 'inflow' ? 'success' : 'danger'" style="margin-left: 8px;">
                  今日{{ flowType === 'inflow' ? '净流入' : '净流出' }}
                </el-tag>
              </span>
              <el-radio-group v-model="flowType" size="small" @change="loadFundFlow">
                <el-radio-button value="inflow">净流入</el-radio-button>
                <el-radio-button value="outflow">净流出</el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <div v-loading="fundFlowLoading" class="fund-flow-list">
            <template v-if="industryFundFlow.length > 0">
              <div
                v-for="item in industryFundFlow"
                :key="item.name"
                class="fund-flow-item"
              >
                <span class="rank" :class="getRankClass(item.rank)">
                  {{ item.rank }}
                </span>
                <span class="name">{{ item.name }}</span>
                <span class="inflow" :class="{ positive: item.inflow > 0, negative: item.inflow < 0 }">
                  {{ formatInflow(item.inflow) }}
                </span>
              </div>
            </template>
            <el-empty v-else description="暂无数据" :image-size="60" />
          </div>
        </el-card>

        <!-- 概念板块资金流 -->
        <el-card class="fund-flow-card" shadow="never" style="margin-top: 16px;">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Collection /></el-icon>
                概念板块资金流
                <el-tag size="small" :type="flowType === 'inflow' ? 'warning' : 'danger'" style="margin-left: 8px;">
                  今日{{ flowType === 'inflow' ? '净流入' : '净流出' }}
                </el-tag>
              </span>
              <el-radio-group v-model="flowType" size="small" @change="loadFundFlow">
                <el-radio-button value="inflow">净流入</el-radio-button>
                <el-radio-button value="outflow">净流出</el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <div v-loading="fundFlowLoading" class="fund-flow-list">
            <template v-if="conceptFundFlow.length > 0">
              <div
                v-for="item in conceptFundFlow"
                :key="item.name"
                class="fund-flow-item"
              >
                <span class="rank" :class="getRankClass(item.rank)">
                  {{ item.rank }}
                </span>
                <span class="name">{{ item.name }}</span>
                <span class="inflow" :class="{ positive: item.inflow > 0, negative: item.inflow < 0 }">
                  {{ formatInflow(item.inflow) }}
                </span>
              </div>
            </template>
            <el-empty v-else description="暂无数据" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  Refresh,
  Document,
  Coin,
  Collection
} from '@element-plus/icons-vue'
import { marketApi } from '@/api/market'
import type { NewsItem, FundFlowItem, FlowType } from '@/api/market'

// 响应式数据
const loading = ref(false)
const fundFlowLoading = ref(false)
const hoursBack = ref(24)
const newsLimit = ref(30)
const updateTime = ref('')
const flowType = ref<FlowType>('inflow')

const newsList = ref<NewsItem[]>([])
const industryFundFlow = ref<FundFlowItem[]>([])
const conceptFundFlow = ref<FundFlowItem[]>([])

// 加载新闻
const loadNews = async () => {
  try {
    const res = await marketApi.getNews(newsLimit.value, hoursBack.value)
    const data = (res as any)?.data
    if (data) {
      newsList.value = data.news || []
    }
  } catch (error: any) {
    console.error('加载新闻失败:', error)
  }
}

// 加载资金流
const loadFundFlow = async () => {
  fundFlowLoading.value = true
  try {
    const res = await marketApi.getOverview(flowType.value)
    const data = (res as any)?.data

    if (data) {
      industryFundFlow.value = data.industry_fund_flow || []
      conceptFundFlow.value = data.concept_fund_flow || []
      updateTime.value = data.update_time || ''
    }
  } catch (error: any) {
    console.error('加载资金流失败:', error)
    ElMessage.error(error.message || '加载数据失败')
  } finally {
    fundFlowLoading.value = false
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([loadNews(), loadFundFlow()])
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await loadData()
  ElMessage.success('数据已刷新')
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return timeStr
  }
}

// 格式化新闻时间
const formatNewsTime = (datetime: string) => {
  if (!datetime) return ''
  try {
    // 格式: "2025-01-15 14:30:00"
    const parts = datetime.split(' ')
    if (parts.length >= 2) {
      const timePart = parts[1].substring(0, 5) // HH:MM
      return timePart
    }
    return datetime
  } catch {
    return datetime
  }
}

// 格式化流入金额
const formatInflow = (value: number) => {
  if (value === null || value === undefined) return '-'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}亿`
}

// 获取排名样式类
const getRankClass = (rank: number) => {
  if (rank === 1) return 'rank-1'
  if (rank === 2) return 'rank-2'
  if (rank === 3) return 'rank-3'
  return ''
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.market-overview {
  .page-header {
    margin-bottom: 24px;

    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;
    }

    .page-description {
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }

  .action-card {
    margin-bottom: 24px;

    .update-time {
      margin-left: 16px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

  .main-content {
    min-height: 600px;
  }

  .news-card {
    height: 100%;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .news-count {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }

    .news-list {
      max-height: 700px;
      overflow-y: auto;
    }

    .news-item {
      display: flex;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .news-time {
        flex-shrink: 0;
        width: 50px;
        font-size: 14px;
        font-weight: 600;
        color: var(--el-text-color-secondary);
        padding-right: 12px;
      }

      .news-content {
        flex: 1;
        min-width: 0;

        .news-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 6px;
          line-height: 1.4;
        }

        .news-text {
          font-size: 14px;
          color: var(--el-text-color-regular);
          line-height: 1.6;
          word-break: break-word;
          white-space: pre-wrap;
        }
      }
    }
  }

  .fund-flow-card {
    .card-header {
      display: flex;
      align-items: center;
    }

    .fund-flow-list {
      max-height: 280px;
      overflow-y: auto;
    }

    .fund-flow-item {
      display: flex;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .rank {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 20px;
        height: 20px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 4px;
        background: var(--el-fill-color-light);
        color: var(--el-text-color-secondary);
        margin-right: 10px;

        &.rank-1 {
          background: #ff4d4f;
          color: #fff;
        }

        &.rank-2 {
          background: #ff7a45;
          color: #fff;
        }

        &.rank-3 {
          background: #ffa940;
          color: #fff;
        }
      }

      .name {
        flex: 1;
        font-size: 14px;
        color: var(--el-text-color-primary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .inflow {
        font-size: 14px;
        font-weight: 600;
        font-family: 'Monaco', 'Menlo', monospace;

        &.positive {
          color: #f5222d;
        }

        &.negative {
          color: #52c41a;
        }
      }
    }
  }
}
</style>
