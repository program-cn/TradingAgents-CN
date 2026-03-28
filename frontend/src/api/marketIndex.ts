/**
 * 市场指数API
 */
import { request } from './request'

export interface IndexQuote {
  code: string
  name: string
  market?: 'CN' | 'HK' | 'US'
  price: number
  change: number
  change_percent: number
  is_up: boolean
  is_down: boolean
  sparkline?: SparklinePoint[]
}

export interface SparklinePoint {
  date: string
  value: number
}

/**
 * 获取主要指数实时行情
 */
export async function getMarketIndexes() {
  return request.get('/api/market/indexes')
}

/**
 * 获取指数历史数据
 */
export async function getIndexHistory(code: string, period: string = '1m') {
  return request.get(`/api/market/index/${code}/history`, {
    params: { period }
  })
}

/**
 * 获取指数及缩略曲线数据（推荐使用，减少请求次数）
 */
export async function getIndexesWithSparkline(period: string = '1m') {
  return request.get('/api/market/indexes/with-sparkline', {
    params: { period }
  })
}

export const marketIndexApi = {
  getMarketIndexes,
  getIndexHistory,
  getIndexesWithSparkline
}
