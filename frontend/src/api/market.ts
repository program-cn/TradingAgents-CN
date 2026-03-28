import { ApiClient } from './request'

export interface NewsItem {
  title: string
  content: string
  datetime: string
  source: string
  hash?: string
}

export interface FundFlowItem {
  rank: number
  name: string
  inflow: number
  unit: string
}

export interface MarketOverviewData {
  news: NewsItem[]
  industry_fund_flow: FundFlowItem[]
  concept_fund_flow: FundFlowItem[]
  flow_type: string
  update_time: string
}

export type FlowType = 'inflow' | 'outflow'

export const marketApi = {
  /**
   * 获取财联社新闻
   */
  getNews: (limit: number = 30, hoursBack: number = 24) =>
    ApiClient.get<{
      news: NewsItem[]
      total_count: number
      update_time: string
    }>('/api/market-overview/news', { limit, hours_back: hoursBack }),

  /**
   * 获取行业资金流排行
   */
  getIndustryFundFlow: (topN: number = 15, flowType: FlowType = 'inflow') =>
    ApiClient.get<{
      industry_fund_flow: FundFlowItem[]
      total_count: number
      flow_type: string
      update_time: string
    }>('/api/market-overview/fund-flow/industry', { top_n: topN, flow_type: flowType }),

  /**
   * 获取概念板块资金流排行
   */
  getConceptFundFlow: (topN: number = 15, flowType: FlowType = 'inflow') =>
    ApiClient.get<{
      concept_fund_flow: FundFlowItem[]
      total_count: number
      flow_type: string
      update_time: string
    }>('/api/market-overview/fund-flow/concept', { top_n: topN, flow_type: flowType }),

  /**
   * 获取市场概览（聚合数据）
   */
  getOverview: (flowType: FlowType = 'inflow') =>
    ApiClient.get<MarketOverviewData>('/api/market-overview/overview', { flow_type: flowType }),
}
