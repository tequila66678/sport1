<template>
  <div class="cockpit">
    <!-- ===== ① Welcome Bar ===== -->
    <div class="welcome-bar">
      <div class="welcome-left">
        <span class="welcome-greeting">{{ greeting }}</span>
        <span class="welcome-divider">|</span>
        <span class="welcome-school">🏫 {{ schoolName }}</span>
        <span class="welcome-divider">|</span>
        <span class="welcome-cohort">📅 本期中考学生：2026届</span>
      </div>
      <div class="welcome-right">
        <span class="today-date">{{ todayStr }}</span>
      </div>
    </div>

    <!-- ===== ② KPI Cards ===== -->
    <div class="section-label">核心指标</div>
    <div class="kpi-grid" v-if="stats">
      <!-- 预测中考满分率 -->
      <div class="kpi-card gold">
        <div class="kpi-label">预计中考满分率</div>
        <div class="kpi-value-row">
          <span class="kpi-value">{{ stats.full_score_rate ?? '--' }}</span>
          <span class="kpi-unit">%</span>
          <span class="kpi-trend" :class="trendsDir.full_score_rate">
            {{ trendsDir.full_score_rate === 'up' ? '↑' : trendsDir.full_score_rate === 'down' ? '↓' : '→' }}
          </span>
        </div>
        <svg class="kpi-spark" :viewBox="'0 0 '+sparkW+' 28'" v-if="sparkFullScore.length">
          <polyline :points="sparkFullScore" fill="none" stroke="#b8860b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          <linearGradient :id="'fsg'" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="#b8860b" stop-opacity="0.15" />
            <stop offset="100%" stop-color="#b8860b" stop-opacity="0" />
          </linearGradient>
          <polygon :points="sparkFullScoreArea" fill="url(#fsg)" />
        </svg>
        <div class="kpi-sub">中考总分=30时计满分</div>
      </div>

      <!-- 预测中考均分 -->
      <div class="kpi-card indigo">
        <div class="kpi-label">预测中考均分</div>
        <div class="kpi-value-row">
          <span class="kpi-value">{{ stats.predicted_avg_score ?? '--' }}</span>
          <span class="kpi-unit">/ 30 分</span>
          <span class="kpi-trend" :class="trendsDir.predicted_avg_score">
            {{ trendsDir.predicted_avg_score === 'up' ? '↑' : trendsDir.predicted_avg_score === 'down' ? '↓' : '→' }}
          </span>
        </div>
        <svg class="kpi-spark" :viewBox="'0 0 '+sparkW+' 28'" v-if="sparkAvg.length">
          <polyline :points="sparkAvg" fill="none" stroke="#4f46e5" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          <linearGradient :id="'avg'" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="#4f46e5" stop-opacity="0.15" />
            <stop offset="100%" stop-color="#4f46e5" stop-opacity="0" />
          </linearGradient>
          <polygon :points="sparkAvgArea" fill="url(#avg)" />
        </svg>
        <div class="kpi-sub">长跑(必考)+最优2项</div>
      </div>

      <!-- 参与率 -->
      <div class="kpi-card amber">
        <div class="kpi-label">参与率</div>
        <div class="kpi-value-row">
          <span class="kpi-value">{{ participationRate }}</span>
          <span class="kpi-unit">%</span>
        </div>
        <div class="kpi-sub">{{ stats.participants ?? 0 }} / {{ stats.total_students ?? 0 }} 名学生参与</div>
      </div>

      <!-- 下滑风险学生 -->
      <div class="kpi-card red-card">
        <div class="kpi-label">下滑风险学生</div>
        <div class="kpi-value-row">
          <span class="kpi-value red-val">{{ stats.warning_students?.length ?? 0 }}</span>
          <span class="kpi-unit">人</span>
        </div>
        <div class="kpi-sub">近两次成绩下滑≥2分</div>
      </div>
    </div>

    <!-- ===== ③ Secondary Stats Bar ===== -->
    <div class="stats-bar" v-if="stats">
      <div class="stat-item">
        <span class="stat-icon">👥</span>
        <span class="stat-label">在校人数</span>
        <span class="stat-num">{{ stats.total_students ?? '--' }}</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-icon">🏃</span>
        <span class="stat-label">本月训练次数</span>
        <span class="stat-num">{{ stats.training_count_this_month ?? '--' }}</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-icon">⚠️</span>
        <span class="stat-label">风险班级</span>
        <span class="stat-num">{{ stats.risk_classes?.length ?? 0 }}</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-icon">📊</span>
        <span class="stat-label">班级总数</span>
        <span class="stat-num">{{ stats.total_classes ?? '--' }}</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-icon">🏅</span>
        <span class="stat-label">满分率</span>
        <span class="stat-num">{{ stats.full_score_rate ?? '--' }}%</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-icon">📈</span>
        <span class="stat-label">平均成绩</span>
        <span class="stat-num">{{ stats.avg_score ?? '--' }}</span>
      </div>
    </div>

    <!-- Loading / Empty -->
    <div v-if="!stats" class="loading-box">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- ===== ④ Charts Row ===== -->
    <div class="section-label">数据分析</div>
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">📈 平均分趋势<span class="chart-subtitle">近6个月</span></div>
        <v-chart :option="trendChartOption" autoresize style="height:280px" v-if="trends.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🕸 项目能力雷达<span class="chart-subtitle">各项目均分</span></div>
        <v-chart :option="radarChartOption" autoresize style="height:280px" v-if="stats?.event_avgs?.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🍩 分数分布<span class="chart-subtitle">中考总分分档</span></div>
        <v-chart :option="donutChartOption" autoresize style="height:280px" v-if="stats?.score_distribution?.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
    </div>

    <!-- ===== ⑤ Bottom Row: Risk + AI ===== -->
    <div class="bottom-grid">
      <!-- Risk students TOP5 -->
      <div class="risk-card">
        <div class="risk-hd">
          <span>🚨 下滑风险学生 TOP{{ Math.min(5, stats?.warning_students?.length || 0) }}</span>
          <span class="risk-badge red">{{ stats?.warning_students?.length || 0 }}人</span>
        </div>
        <div class="risk-list" v-if="stats?.warning_students?.length">
          <div class="risk-row" v-for="(w, i) in stats.warning_students.slice(0, 5)" :key="i">
            <span class="risk-rank" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
            <div class="risk-info">
              <span class="risk-name">{{ w.student_name }}</span>
              <span class="risk-meta-inline"> · {{ w.class_name }} · {{ w.event_name }}</span>
            </div>
            <span class="risk-decline">↓{{ (w.prev_score - w.curr_score).toFixed(1) }}</span>
            <span class="risk-scores">{{ w.prev_score }}→{{ w.curr_score }}</span>
          </div>
        </div>
        <div v-else class="risk-empty">✅ 暂无下滑风险学生</div>
      </div>

      <!-- AI Analysis -->
      <div class="ai-card">
        <div class="ai-hd">
          <span>💡 AI 分析建议</span>
          <span class="ai-badge">自动分析</span>
        </div>
        <div class="ai-body">
          <div class="ai-item" v-for="(tip, i) in aiTips" :key="i">
            <span class="ai-dot" :class="tip.type"></span>
            <span>{{ tip.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { LineChart, PieChart, RadarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent, PolarComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import api from '../../api'

use([LineChart, PieChart, RadarChart, CanvasRenderer, TitleComponent, TooltipComponent, GridComponent, LegendComponent, PolarComponent])

// ===== State =====
const stats = ref(null)
const trends = ref([])

const sparkW = 120

// ===== Computed =====
const todayStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '🌙 夜深了，船长'
  if (h < 9) return '🌅 早上好，船长'
  if (h < 12) return '☀️ 上午好，船长'
  if (h < 14) return '🌤 中午好，船长'
  if (h < 18) return '👋 下午好，船长'
  return '🌆 晚上好，船长'
})

const schoolName = computed(() => {
  const info = localStorage.getItem('admin_info')
  if (info) {
    try { return JSON.parse(info).school_name || '体育成绩管理系统' } catch {}
  }
  return '体育成绩管理系统'
})

const participationRate = computed(() => {
  if (!stats.value) return '--'
  const { participants, total_students } = stats.value
  if (!total_students) return '0'
  return Math.round(participants / total_students * 100)
})

// Trend directions by comparing first half vs second half
const trendsDir = computed(() => {
  const dirs = { predicted_avg_score: 'flat', full_score_rate: 'flat' }
  if (trends.value.length < 2) return dirs
  const half = Math.floor(trends.value.length / 2)
  const first = trends.value.slice(0, half)
  const second = trends.value.slice(half)
  const firstAvg = first.reduce((s, t) => s + t.predicted_avg_score, 0) / first.length
  const secondAvg = second.reduce((s, t) => s + t.predicted_avg_score, 0) / second.length
  if (secondAvg > firstAvg + 0.3) dirs.predicted_avg_score = 'up'
  else if (secondAvg < firstAvg - 0.3) dirs.predicted_avg_score = 'down'
  const firstFS = first.reduce((s, t) => s + t.full_score_rate, 0) / first.length
  const secondFS = second.reduce((s, t) => s + t.full_score_rate, 0) / second.length
  if (secondFS > firstFS + 1) dirs.full_score_rate = 'up'
  else if (secondFS < firstFS - 1) dirs.full_score_rate = 'down'
  return dirs
})

// Sparkline: normalized polyline points from trends
function buildSpark(data, key) {
  if (!data.length) return { line: '', area: '' }
  const values = data.map(d => d[key] || 0)
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = max - min || 1
  const h = 24
  const pad = 2
  const step = (sparkW - pad * 2) / Math.max(values.length - 1, 1)

  const pts = values.map((v, i) => {
    const x = (pad + i * step).toFixed(1)
    const y = (h - ((v - min) / range) * (h - pad * 2) - pad).toFixed(1)
    return `${x},${y}`
  })
  const line = pts.join(' ')
  const area = pts[0] + ' ' + pts.join(' ') + ' ' + (pad + (values.length - 1) * step).toFixed(1) + ',' + (h + 2) + ' ' + pad.toFixed(1) + ',' + (h + 2)
  return { line, area }
}

const sparkAvg = computed(() => buildSpark(trends.value, 'predicted_avg_score').line)
const sparkAvgArea = computed(() => buildSpark(trends.value, 'predicted_avg_score').area)
const sparkFullScore = computed(() => buildSpark(trends.value, 'full_score_rate').line)
const sparkFullScoreArea = computed(() => buildSpark(trends.value, 'full_score_rate').area)

// ===== Chart Options =====
const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 16, bottom: 28 },
  xAxis: {
    type: 'category',
    data: trends.value.map(t => t.month?.slice(2) || t.month),
    axisLine: { lineStyle: { color: '#e8e6e1' } },
    axisTick: { show: false },
    axisLabel: { color: '#a3a3a3', fontSize: 10 }
  },
  yAxis: {
    type: 'value',
    min: 0, max: 30,
    splitLine: { lineStyle: { color: '#f0ede8', type: 'dashed' } },
    axisLabel: { color: '#a3a3a3', fontSize: 10 }
  },
  series: [{
    type: 'line',
    data: trends.value.map(t => t.predicted_avg_score),
    smooth: true,
    lineStyle: { color: '#4f46e5', width: 2.5 },
    itemStyle: { color: '#4f46e5' },
    symbol: 'circle', symbolSize: 5,
    areaStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(79,70,229,0.12)' },
          { offset: 1, color: 'rgba(79,70,229,0)' }
        ]
      }
    }
  }]
}))

const radarChartOption = computed(() => {
  const events = stats.value?.event_avgs || []
  return {
    tooltip: {},
    legend: { show: false },
    radar: {
      center: ['50%', '52%'],
      radius: '62%',
      indicator: events.map(e => ({ name: e.event_name, max: 10 })),
      axisName: { color: '#525252', fontSize: 10, borderRadius: 3, padding: [3, 5] },
      splitArea: { areaStyle: { color: ['rgba(79,70,229,0.02)', 'rgba(79,70,229,0.02)'] } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: events.map(e => e.avg_score),
        name: '均分',
        lineStyle: { color: '#4f46e5', width: 2 },
        areaStyle: { color: 'rgba(79,70,229,0.1)' },
        itemStyle: { color: '#4f46e5' },
        symbol: 'circle', symbolSize: 4
      }]
    }]
  }
})

const donutChartOption = computed(() => {
  const buckets = stats.value?.score_distribution || []
  const colors = ['#4f46e5', '#7c75f0', '#a5a0f5', '#cdc9fa', '#e8e6e1']
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 10, color: '#525252' } },
    series: [{
      type: 'pie',
      radius: ['48%', '74%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } },
      data: buckets.map((b, i) => ({
        value: b.count,
        name: b.label,
        itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  }
})

// AI tips based on data patterns
const aiTips = computed(() => {
  const tips = []
  if (!stats.value) return tips

  // Check trend direction
  const avgDir = trendsDir.value.predicted_avg_score
  const fsDir = trendsDir.value.full_score_rate

  if (avgDir === 'up') {
    tips.push({ type: 'good', text: `均分趋势持续上升，训练计划执行良好，继续保持当前节奏。` })
  } else if (avgDir === 'down') {
    tips.push({ type: 'warn', text: `均分呈下降趋势，建议排查近期训练强度是否不足或测试标准是否调整。` })
  }

  if (fsDir === 'up') {
    tips.push({ type: 'good', text: `满分率稳步提升，优秀学生群体在扩大，尖子生培养策略有效。` })
  } else if (fsDir === 'down') {
    tips.push({ type: 'warn', text: `满分率下滑，关注高分段学生的成绩波动，必要时进行针对性辅导。` })
  }

  // Risk events
  if (stats.value.risk_events?.length) {
    const worst = stats.value.risk_events[0]
    tips.push({ type: 'warn', text: `「${worst.event_name}」为全校最薄弱项目（均分${worst.avg_score}），建议纳入重点训练计划。` })
  }

  // Risk classes
  if (stats.value.risk_classes?.length) {
    const worstClass = stats.value.risk_classes[0]
    tips.push({ type: 'info', text: `「${worstClass.class_name}」中考预测均分最低（${worstClass.predicted_avg_score}分），建议重点关注该班训练质量。` })
  }

  // Participation
  if (stats.value.participants && stats.value.total_students) {
    const rate = stats.value.participants / stats.value.total_students * 100
    if (rate < 70) {
      tips.push({ type: 'warn', text: `参与率仅${Math.round(rate)}%，较多学生未在近30天有测试记录，请尽快安排补测。` })
    }
  }

  // Warning students
  const wCount = stats.value.warning_students?.length || 0
  if (wCount >= 10) {
    tips.push({ type: 'warn', text: `${wCount}名学生出现成绩下滑（≥2分），建议逐一沟通了解原因并及时干预。` })
  } else if (wCount === 0) {
    tips.push({ type: 'good', text: `无成绩下滑风险学生，整体训练效果稳定，值得肯定！` })
  }

  if (tips.length === 0) {
    tips.push({ type: 'info', text: '数据量较少，随着更多测试数据录入，系统将提供更精准的分析建议。' })
  }
  return tips
})

// ===== Data Fetching =====
async function loadData() {
  try {
    const [statsRes, trendsRes] = await Promise.all([
      api.get('/scores/school-stats'),
      api.get('/scores/trends')
    ])
    stats.value = statsRes.data
    trends.value = trendsRes.data || []
  } catch (e) {
    console.error('Dashboard load error:', e)
  }
}

onMounted(loadData)
</script>

<style scoped>
/* ===== Design Tokens ===== */
.cockpit {
  --bg-root: #f6f5f3;
  --border: #e8e6e1;
  --indigo: #4f46e5;
  --gold: #b8860b;
  --amber: #d97706;
  --red: #dc2626;
  --text-a: #171717;
  --text-b: #525252;
  --text-c: #a3a3a3;
  max-width: 1280px;
}

/* ===== Welcome Bar ===== */
.welcome-bar {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  background: linear-gradient(135deg, #fff 0%, #fafaf9 100%);
  border: 1px solid var(--border); border-radius: 14px;
  padding: 14px 20px; margin-bottom: 18px;
}
.welcome-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.welcome-greeting { font-size: 15px; font-weight: 700; color: var(--text-a); }
.welcome-divider { color: #d4d0c8; font-size: 14px; }
.welcome-school { font-size: 12.5px; color: var(--text-b); }
.welcome-cohort { font-size: 12px; color: var(--text-c); }
.welcome-right { display: flex; align-items: center; gap: 12px; }
.today-date { font-size: 11.5px; color: var(--text-c); }

/* ===== KPI Grid ===== */
.section-label {
  font-size: 12px; font-weight: 700; color: var(--text-b);
  letter-spacing: 0.5px; text-transform: uppercase;
  margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 16px;
}
@media (max-width: 1000px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px) { .kpi-grid { grid-template-columns: 1fr; } }

.kpi-card {
  background: #fff; border: 1px solid var(--border); border-radius: 16px;
  padding: 18px 20px 10px; position: relative; overflow: hidden;
  transition: all 0.2s;
}
.kpi-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-1px); }
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 14px; right: 14px;
  height: 3px; border-radius: 0 0 3px 3px;
}
.kpi-card.indigo::before { background: var(--indigo); }
.kpi-card.gold::before { background: var(--gold); }
.kpi-card.amber::before { background: var(--amber); }
.kpi-card.red-card::before { background: var(--red); }

.kpi-label {
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.8px;
  color: var(--text-c); text-transform: uppercase; margin-bottom: 3px;
}
.kpi-value-row { display: flex; align-items: baseline; gap: 4px; }
.kpi-value { font-size: 34px; font-weight: 800; letter-spacing: -1px; line-height: 1; }
.kpi-card.indigo .kpi-value { color: var(--indigo); }
.kpi-card.gold .kpi-value { color: var(--gold); }
.kpi-card.amber .kpi-value { color: var(--amber); }
.kpi-card.red-card .kpi-value { color: var(--red); }
.kpi-unit { font-size: 13px; font-weight: 500; color: var(--text-c); }
.kpi-trend { font-size: 16px; font-weight: 700; margin-left: 2px; }
.kpi-trend.up { color: #16a34a; }
.kpi-trend.down { color: var(--red); }
.kpi-trend.flat { color: var(--text-c); }

.kpi-spark { width: 100%; height: 26px; margin-top: 4px; display: block; }
.kpi-sub { margin-top: 2px; font-size: 10px; color: var(--text-c); }

/* ===== Stats Bar ===== */
.stats-bar {
  display: flex; align-items: center; flex-wrap: wrap; gap: 0;
  background: #fff; border: 1px solid var(--border); border-radius: 12px;
  padding: 10px 8px; margin-bottom: 20px;
}
.stat-item {
  display: flex; align-items: center; gap: 6px; padding: 4px 12px;
  flex: 1; min-width: 100px; justify-content: center;
}
.stat-icon { font-size: 15px; flex-shrink: 0; }
.stat-label { font-size: 11px; color: var(--text-c); white-space: nowrap; }
.stat-num { font-size: 15px; font-weight: 700; color: var(--text-a); }
.stat-divider { width: 1px; height: 24px; background: var(--border); flex-shrink: 0; }
@media (max-width: 768px) { .stat-divider { display: none; } }

/* ===== Charts Grid ===== */
.charts-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 12px; margin-bottom: 16px;
}
@media (max-width: 1000px) { .charts-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 650px) { .charts-grid { grid-template-columns: 1fr; } }

.chart-card {
  background: #fff; border: 1px solid var(--border); border-radius: 16px;
  padding: 16px 18px 10px;
}
.chart-title { font-size: 13px; font-weight: 600; color: var(--text-a); margin-bottom: 4px; }
.chart-subtitle { font-weight: 400; font-size: 10px; color: var(--text-c); margin-left: 6px; }
.chart-empty { height: 200px; display: flex; align-items: center; justify-content: center; color: var(--text-c); font-size: 13px; }

/* ===== Bottom Grid ===== */
.bottom-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px; margin-bottom: 16px;
}
@media (max-width: 768px) { .bottom-grid { grid-template-columns: 1fr; } }

/* Risk Card */
.risk-card {
  background: #fff; border: 1px solid var(--border); border-radius: 16px; overflow: hidden;
}
.risk-hd {
  padding: 14px 20px; border-bottom: 1px solid var(--border);
  font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: space-between;
}
.risk-badge { padding: 2px 10px; border-radius: 12px; font-size: 10px; font-weight: 700; }
.risk-badge.red { background: #fef2f2; color: var(--red); }

.risk-list { padding: 4px 0; }
.risk-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; transition: background 0.15s;
}
.risk-row:hover { background: #fafaf9; }
.risk-rank { width: 20px; text-align: center; font-size: 11px; font-weight: 700; color: var(--text-c); flex-shrink: 0; }
.risk-rank.top3 { color: var(--amber); }
.risk-info { flex: 1; min-width: 0; }
.risk-name { font-size: 12.5px; font-weight: 600; color: var(--text-a); }
.risk-meta-inline { font-weight: 400; font-size: 10px; color: var(--text-c); }
.risk-decline { font-size: 13px; font-weight: 700; color: var(--red); flex-shrink: 0; }
.risk-scores { font-size: 10px; color: var(--text-c); flex-shrink: 0; width: 42px; text-align: right; }
.risk-empty { padding: 32px 20px; text-align: center; color: var(--text-c); font-size: 13px; }

/* AI Card */
.ai-card {
  background: #fff; border: 1px solid var(--border); border-radius: 16px; overflow: hidden;
}
.ai-hd {
  padding: 14px 20px; border-bottom: 1px solid var(--border);
  font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: space-between;
}
.ai-badge {
  padding: 2px 10px; border-radius: 12px; font-size: 10px; font-weight: 700;
  background: #eff6ff; color: var(--indigo);
}
.ai-body { padding: 12px 20px 16px; }
.ai-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 0; font-size: 12.5px; color: var(--text-b); line-height: 1.55;
}
.ai-item + .ai-item { border-top: 1px solid #f5f3f0; }
.ai-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
.ai-dot.good { background: #16a34a; }
.ai-dot.warn { background: var(--amber); }
.ai-dot.info { background: var(--indigo); }

.loading-box { padding: 24px; }
</style>
