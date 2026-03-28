<template>
  <el-card class="market-index-card">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <el-icon><TrendCharts /></el-icon>
          <span>市场指数</span>
        </div>
        <div class="header-right">
          <el-radio-group v-model="selectedPeriod" size="small" @change="loadData">
            <el-radio-button label="1d">1天</el-radio-button>
            <el-radio-button label="1w">1周</el-radio-button>
            <el-radio-button label="1m">1月</el-radio-button>
            <el-radio-button label="1y">1年</el-radio-button>
          </el-radio-group>
          <el-button 
            :icon="RefreshRight" 
            circle 
            size="small" 
            :loading="loading"
            @click="loadData"
            style="margin-left: 8px;"
          />
        </div>
      </div>
    </template>

    <div v-if="loading && indexes.length === 0" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="indexes.length === 0" class="empty-state">
      <el-icon class="empty-icon"><WarningFilled /></el-icon>
      <p>暂无指数数据</p>
      <el-button type="primary" size="small" @click="loadData">重新加载</el-button>
    </div>

    <template v-else>
      <!-- A股指数 -->
      <div class="market-section" v-if="cnIndexes.length > 0">
        <div class="market-title">
          <span class="market-badge cn">A股</span>
        </div>
        <div class="index-grid">
          <div 
            v-for="index in cnIndexes" 
            :key="index.code" 
            class="index-item"
            :class="{ 'is-up': index.is_up, 'is-down': index.is_down }"
          >
            <div class="index-info">
              <div class="index-name">{{ index.name }}</div>
              <div class="index-code">{{ index.code }}</div>
            </div>
            
            <div class="index-price-section">
              <div class="index-price" :class="getPriceClass(index)">
                {{ formatPrice(index.price) }}
              </div>
              <div class="index-change" :class="getPriceClass(index)">
                <span class="change-value">{{ index.change > 0 ? '+' : '' }}{{ formatPrice(index.change) }}</span>
                <span class="change-percent">({{ index.change_percent > 0 ? '+' : '' }}{{ index.change_percent }}%)</span>
              </div>
            </div>

            <!-- 缩略曲线 -->
            <div class="sparkline-container">
              <svg 
                v-if="index.sparkline && index.sparkline.length > 1"
                :viewBox="`0 0 ${sparklineWidth} ${sparklineHeight}`"
                class="sparkline"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient :id="`gradient-${index.code}`" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" :stop-color="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'" stop-opacity="0.3"/>
                    <stop offset="100%" :stop-color="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'" stop-opacity="0"/>
                  </linearGradient>
                </defs>
                <path :d="getAreaPath(index.sparkline)" :fill="`url(#gradient-${index.code})`" />
                <path 
                  :d="getLinePath(index.sparkline)"
                  fill="none"
                  :stroke="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <div v-else class="sparkline-placeholder">
                <el-icon><TrendCharts /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 港股指数 -->
      <div class="market-section" v-if="hkIndexes.length > 0">
        <div class="market-title">
          <span class="market-badge hk">港股</span>
        </div>
        <div class="index-grid">
          <div 
            v-for="index in hkIndexes" 
            :key="index.code" 
            class="index-item"
            :class="{ 'is-up': index.is_up, 'is-down': index.is_down }"
          >
            <div class="index-info">
              <div class="index-name">{{ index.name }}</div>
              <div class="index-code">{{ index.code }}</div>
            </div>
            
            <div class="index-price-section">
              <div class="index-price" :class="getPriceClass(index)">
                {{ formatPrice(index.price) }}
              </div>
              <div class="index-change" :class="getPriceClass(index)">
                <span class="change-value">{{ index.change > 0 ? '+' : '' }}{{ formatPrice(index.change) }}</span>
                <span class="change-percent">({{ index.change_percent > 0 ? '+' : '' }}{{ index.change_percent }}%)</span>
              </div>
            </div>

            <div class="sparkline-container">
              <svg 
                v-if="index.sparkline && index.sparkline.length > 1"
                :viewBox="`0 0 ${sparklineWidth} ${sparklineHeight}`"
                class="sparkline"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient :id="`gradient-${index.code}`" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" :stop-color="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'" stop-opacity="0.3"/>
                    <stop offset="100%" :stop-color="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'" stop-opacity="0"/>
                  </linearGradient>
                </defs>
                <path :d="getAreaPath(index.sparkline)" :fill="`url(#gradient-${index.code})`" />
                <path 
                  :d="getLinePath(index.sparkline)"
                  fill="none"
                  :stroke="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <div v-else class="sparkline-placeholder">
                <el-icon><TrendCharts /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 美股指数 -->
      <div class="market-section" v-if="usIndexes.length > 0">
        <div class="market-title">
          <span class="market-badge us">美股</span>
        </div>
        <div class="index-grid">
          <div 
            v-for="index in usIndexes" 
            :key="index.code" 
            class="index-item"
            :class="{ 'is-up': index.is_up, 'is-down': index.is_down }"
          >
            <div class="index-info">
              <div class="index-name">{{ index.name }}</div>
              <div class="index-code">{{ index.code }}</div>
            </div>
            
            <div class="index-price-section">
              <div class="index-price" :class="getPriceClass(index)">
                {{ formatPrice(index.price) }}
              </div>
              <div class="index-change" :class="getPriceClass(index)">
                <span class="change-value">{{ index.change > 0 ? '+' : '' }}{{ formatPrice(index.change) }}</span>
                <span class="change-percent">({{ index.change_percent > 0 ? '+' : '' }}{{ index.change_percent }}%)</span>
              </div>
            </div>

            <div class="sparkline-container">
              <svg 
                v-if="index.sparkline && index.sparkline.length > 1"
                :viewBox="`0 0 ${sparklineWidth} ${sparklineHeight}`"
                class="sparkline"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient :id="`gradient-${index.code}`" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" :stop-color="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'" stop-opacity="0.3"/>
                    <stop offset="100%" :stop-color="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'" stop-opacity="0"/>
                  </linearGradient>
                </defs>
                <path :d="getAreaPath(index.sparkline)" :fill="`url(#gradient-${index.code})`" />
                <path 
                  :d="getLinePath(index.sparkline)"
                  fill="none"
                  :stroke="index.is_up ? '#f56c6c' : index.is_down ? '#67c23a' : '#909399'"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <div v-else class="sparkline-placeholder">
                <el-icon><TrendCharts /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div class="update-time" v-if="lastUpdate">
      <el-icon><Clock /></el-icon>
      <span>更新于 {{ lastUpdate }}</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { TrendCharts, RefreshRight, WarningFilled, Clock } from '@element-plus/icons-vue'
import { marketIndexApi, type IndexQuote } from '@/api/marketIndex'
import { ElMessage } from 'element-plus'

// 响应式数据
const loading = ref(false)
const indexes = ref<IndexQuote[]>([])
const selectedPeriod = ref('1m')
const lastUpdate = ref('')
const sparklineWidth = 120
const sparklineHeight = 40

// 自动刷新定时器
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 按市场分类
const cnIndexes = computed(() => indexes.value.filter(i => i.market === 'CN' || !i.market))
const hkIndexes = computed(() => indexes.value.filter(i => i.market === 'HK'))
const usIndexes = computed(() => indexes.value.filter(i => i.market === 'US'))

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const response = await marketIndexApi.getIndexesWithSparkline(selectedPeriod.value)
    if (response.success && response.data) {
      indexes.value = response.data
      lastUpdate.value = new Date().toLocaleTimeString('zh-CN')
    } else {
      console.warn('获取指数数据失败:', response.message)
    }
  } catch (error) {
    console.error('获取指数数据失败:', error)
    ElMessage.error('获取市场指数失败')
  } finally {
    loading.value = false
  }
}

// 格式化价格
const formatPrice = (price: number) => {
  if (!price && price !== 0) return '--'
  return price.toFixed(2)
}

// 获取价格样式类
const getPriceClass = (index: IndexQuote) => {
  if (index.is_up) return 'price-up'
  if (index.is_down) return 'price-down'
  return 'price-neutral'
}

// 计算缩略图路径
const getLinePath = (data: { value: number }[]) => {
  if (!data || data.length < 2) return ''
  
  const values = data.map(d => d.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * sparklineWidth
    const y = sparklineHeight - ((d.value - min) / range) * (sparklineHeight - 4) - 2
    return `${x},${y}`
  })
  
  return `M ${points.join(' L ')}`
}

// 计算填充区域路径
const getAreaPath = (data: { value: number }[]) => {
  if (!data || data.length < 2) return ''
  
  const values = data.map(d => d.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * sparklineWidth
    const y = sparklineHeight - ((d.value - min) / range) * (sparklineHeight - 4) - 2
    return `${x},${y}`
  })
  
  return `M 0,${sparklineHeight} L ${points.join(' L ')} L ${sparklineWidth},${sparklineHeight} Z`
}

// 生命周期
onMounted(() => {
  loadData()
  // 每60秒自动刷新
  refreshTimer = setInterval(loadData, 60000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style lang="scss" scoped>
.market-index-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      font-size: 16px;
    }

    .header-right {
      display: flex;
      align-items: center;
    }
  }

  .loading-container {
    padding: 24px;
  }

  .empty-state {
    text-align: center;
    padding: 32px 16px;
    color: var(--el-text-color-secondary);

    .empty-icon {
      font-size: 48px;
      color: var(--el-text-color-placeholder);
      margin-bottom: 12px;
    }

    p {
      margin-bottom: 16px;
    }
  }

  .market-section {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }

    .market-title {
      margin-bottom: 12px;
      
      .market-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        
        &.cn {
          background: linear-gradient(135deg, #e74c3c, #c0392b);
          color: white;
        }
        
        &.hk {
          background: linear-gradient(135deg, #3498db, #2980b9);
          color: white;
        }
        
        &.us {
          background: linear-gradient(135deg, #2ecc71, #27ae60);
          color: white;
        }
      }
    }
  }

  .index-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }

  .index-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    background: var(--el-fill-color-blank);
    transition: all 0.3s ease;

    &:hover {
      border-color: var(--el-color-primary-light-5);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }

    &.is-up {
      border-left: 3px solid #f56c6c;
    }

    &.is-down {
      border-left: 3px solid #67c23a;
    }

    .index-info {
      flex-shrink: 0;
      min-width: 80px;

      .index-name {
        font-weight: 600;
        font-size: 15px;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }

      .index-code {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }

    .index-price-section {
      flex-shrink: 0;
      text-align: right;
      margin-right: 12px;

      .index-price {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 4px;

        &.price-up {
          color: #f56c6c;
        }

        &.price-down {
          color: #67c23a;
        }

        &.price-neutral {
          color: var(--el-text-color-primary);
        }
      }

      .index-change {
        font-size: 12px;

        &.price-up {
          color: #f56c6c;
        }

        &.price-down {
          color: #67c23a;
        }

        &.price-neutral {
          color: var(--el-text-color-secondary);
        }

        .change-value {
          font-weight: 500;
        }

        .change-percent {
          margin-left: 2px;
        }
      }
    }

    .sparkline-container {
      width: 120px;
      height: 40px;
      flex-shrink: 0;

      .sparkline {
        width: 100%;
        height: 100%;
      }

      .sparkline-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--el-text-color-placeholder);
        background: var(--el-fill-color-lighter);
        border-radius: 4px;
      }
    }
  }

  .update-time {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--el-border-color-lighter);
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .market-index-card {
    .card-header {
      .header-right {
        width: 100%;
        justify-content: space-between;
      }
    }

    .index-grid {
      grid-template-columns: 1fr;
    }

    .index-item {
      flex-wrap: wrap;

      .sparkline-container {
        width: 100%;
        margin-top: 12px;
        height: 60px;
      }
    }
  }
}
</style>
