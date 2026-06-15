<template>
  <div class="cockpit">
    <!-- ===== ① HEADER ===== -->
    <header class="header">
      <div class="header-left">
        <span class="header-logo">🏫 体育成绩管理系统</span>
        <span class="header-badge">Captain Mode</span>
      </div>
      <div class="header-center">
        <div class="header-greet">{{ greeting }}</div>
        <div class="header-sub">{{ schoolName }} ｜ 本期中考学生：2026届</div>
      </div>
      <div class="header-right">
        <span class="hdr-icon" title="通知">🔔<span class="dot"></span></span>
        <span class="hdr-icon" title="切换学校" @click="$router.push('/admin/settings')">🏫</span>
        <span class="hdr-avatar">{{ avatarChar }}</span>
      </div>
    </header>

    <!-- ===== ② KPI CARDS ===== -->
    <div class="section-label">核心决策指标</div>
    <section class="kpi-grid" v-if="stats">
      <!-- 满分率 · cyan -->
      <div class="kpi-card cyan">
        <div class="kpi-label">预计中考满分率</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ stats.full_score_rate ?? '--' }}</span>
          <span class="kpi-unit">%</span>
          <span class="kpi-delta" :class="trendsDir.full_score_rate">
            <span class="kpi-arrow">{{ trendsDir.full_score_rate === 'up' ? '↑' : trendsDir.full_score_rate === 'down' ? '↓' : '→' }}</span>
            {{ trendsDir.full_score_rate === 'up' ? '上升' : trendsDir.full_score_rate === 'down' ? '下降' : '持平' }}
          </span>
        </div>
        <svg class="kpi-spark" viewBox="0 0 100 24" v-if="sparkFullScore.line">
          <polyline :points="sparkFullScore.line" fill="none" stroke="#06b6d4" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          <linearGradient id="sp1g"><stop offset="0%" stop-color="#06b6d4" stop-opacity="0.18"/><stop offset="100%" stop-color="#06b6d4" stop-opacity="0"/></linearGradient>
          <polygon :points="sparkFullScore.area" fill="url(#sp1g)"/>
        </svg>
        <div class="kpi-sub">中考总分=30时为满分</div>
      </div>

      <!-- 预测均分 · amber -->
      <div class="kpi-card amber">
        <div class="kpi-label">预测中考均分</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ stats.predicted_avg_score ?? '--' }}</span>
          <span class="kpi-unit">/30</span>
          <span class="kpi-delta" :class="trendsDir.predicted_avg_score">
            <span class="kpi-arrow">{{ trendsDir.predicted_avg_score === 'up' ? '↑' : trendsDir.predicted_avg_score === 'down' ? '↓' : '→' }}</span>
            {{ trendsDir.predicted_avg_score === 'up' ? '上升' : trendsDir.predicted_avg_score === 'down' ? '下降' : '持平' }}
          </span>
        </div>
        <svg class="kpi-spark" viewBox="0 0 100 24" v-if="sparkAvg.line">
          <polyline :points="sparkAvg.line" fill="none" stroke="#f59e0b" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          <linearGradient id="sp2g"><stop offset="0%" stop-color="#f59e0b" stop-opacity="0.18"/><stop offset="100%" stop-color="#f59e0b" stop-opacity="0"/></linearGradient>
          <polygon :points="sparkAvg.area" fill="url(#sp2g)"/>
        </svg>
        <div class="kpi-sub">长跑(必考)+最优2项</div>
      </div>

      <!-- 参与率 · emerald -->
      <div class="kpi-card emerald">
        <div class="kpi-label">测试参与率</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ participationRate }}</span>
          <span class="kpi-unit">%</span>
        </div>
        <div class="kpi-sub">{{ stats.participants ?? 0 }} / {{ stats.total_students ?? 0 }} 名学生已参与</div>
      </div>

      <!-- 风险学生 · red -->
      <div class="kpi-card red">
        <div class="kpi-label">下滑风险学生</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ stats.warning_students?.length ?? 0 }}</span>
          <span class="kpi-unit">人</span>
          <span class="kpi-delta down" v-if="stats.warning_students?.length"><span class="kpi-arrow">⚠</span>预警</span>
        </div>
        <div v-if="stats.warning_students?.length" style="display:flex;align-items:flex-end;gap:3px;height:28px;margin-top:6px;padding:0 2px;">
          <div v-for="(h, i) in riskBars" :key="i"
            :style="{flex:1, height:h+'%', background:'#ef4444', opacity:0.35+h*0.01, borderRadius:'2px 2px 0 0'}"
          />
        </div>
        <div v-else style="height:28px;margin-top:6px;display:flex;align-items:center;justify-content:center;color:#64748b;font-size:10px;">✅ 暂无下滑风险</div>
        <div class="kpi-sub">近两次成绩下滑≥2分</div>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="!stats" class="loading-box" style="display:flex;gap:12px;margin-bottom:22px">
      <div v-for="i in 4" :key="i" style="flex:1;height:140px;background:#132238;border-radius:14px;border:1px solid #1e3a5f;animation:pulse 1.5s infinite" />
    </div>

    <!-- ===== ③ STATS BAR ===== -->
    <section class="stats-bar" v-if="stats">
      <div class="stat-item">
        <span class="stat-icon">👥</span><span class="stat-label">在校人数</span><span class="stat-num">{{ stats.total_students?.toLocaleString() ?? '--' }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">🏃</span><span class="stat-label">本月训练次数</span><span class="stat-num">{{ (stats.training_count_this_month || 0).toLocaleString() }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">⚠️</span><span class="stat-label">风险班级</span><span class="stat-num">{{ stats.risk_classes?.length ?? 0 }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">📊</span><span class="stat-label">班级总数</span><span class="stat-num">{{ stats.total_classes ?? '--' }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">🏅</span><span class="stat-label">满分率</span><span class="stat-num">{{ stats.full_score_rate ?? '--' }}%</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">📈</span><span class="stat-label">平均成绩</span><span class="stat-num">{{ stats.avg_score ?? '--' }}</span>
      </div>
    </section>

    <!-- ===== ④ CHARTS ===== -->
    <div class="section-label">多维数据分析</div>
    <section class="charts-grid" v-if="stats">
      <div class="chart-card">
        <div class="chart-title">📈 平均分趋势<span class="chart-sub">近6个月</span></div>
        <v-chart :option="trendChartOption" autoresize style="height:260px" v-if="trends.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🕸 项目能力雷达<span class="chart-sub">各项目均分</span></div>
        <v-chart :option="radarChartOption" autoresize style="height:260px" v-if="stats?.event_avgs?.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🍩 分数分布<span class="chart-sub">中考总分分档</span></div>
        <v-chart :option="donutChartOption" autoresize style="height:260px" v-if="stats?.score_distribution?.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
    </section>

    <!-- ===== ⑤ BOTTOM ===== -->
    <section class="bottom-grid" v-if="stats">
      <!-- Risk students -->
      <div class="risk-card">
        <div class="risk-hd">
          <span>🚨 下滑风险学生 TOP{{ Math.min(5, stats?.warning_students?.length || 0) }}</span>
          <span class="risk-badge" :class="stats?.warning_students?.length ? 'red' : 'good'">{{ stats?.warning_students?.length || 0 }}人</span>
        </div>
        <div class="risk-list" v-if="stats?.warning_students?.length">
          <div class="risk-row" v-for="(w, i) in stats.warning_students.slice(0, 5)" :key="i">
            <span class="risk-rank" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
            <div class="risk-info">
              <span class="risk-name">{{ w.student_name }}</span>
              <span class="risk-meta">{{ w.class_name }} · {{ w.event_name }}</span>
            </div>
            <span class="risk-decline">↓{{ (w.prev_score - w.curr_score).toFixed(1) }}</span>
            <span class="risk-detail">{{ w.prev_score }}→{{ w.curr_score }}</span>
          </div>
        </div>
        <div v-else class="risk-empty">✅ 暂无下滑风险学生</div>
      </div>

      <!-- AI Analysis -->
      <div class="ai-card">
        <div class="ai-hd">
          <span>💡 AI 智能分析</span>
          <span class="ai-badge">实时分析</span>
        </div>
        <div class="ai-body">
          <div class="ai-item" v-for="(tip, i) in aiTips" :key="i">
            <span class="ai-dot" :class="tip.type"></span>
            <span v-html="tip.text"></span>
          </div>
        </div>
      </div>
    </section>
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

// ===== Computed =====
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
  try {
    const info = JSON.parse(localStorage.getItem('admin_info') || '{}')
    return info.school_name || '体育成绩管理系统'
  } catch { return '体育成绩管理系统' }
})

const avatarChar = computed(() => {
  try {
    const info = JSON.parse(localStorage.getItem('admin_info') || '{}')
    return (info.display_name || '管')[0]
  } catch { return '管' }
})

const participationRate = computed(() => {
  if (!stats.value) return '--'
  const { participants, total_students } = stats.value
  if (!total_students) return '0'
  return Math.round(participants / total_students * 100)
})

// Trend direction: compare first half vs second half
const trendsDir = computed(() => {
  const dirs = { predicted_avg_score: 'flat', full_score_rate: 'flat' }
  if (trends.value.length < 2) return dirs
  const half = Math.floor(trends.value.length / 2)
  const first = trends.value.slice(0, half)
  const second = trends.value.slice(half)
  const a1 = first.reduce((s, t) => s + t.predicted_avg_score, 0) / first.length
  const a2 = second.reduce((s, t) => s + t.predicted_avg_score, 0) / second.length
  if (a2 > a1 + 0.3) dirs.predicted_avg_score = 'up'
  else if (a2 < a1 - 0.3) dirs.predicted_avg_score = 'down'
  const f1 = first.reduce((s, t) => s + t.full_score_rate, 0) / first.length
  const f2 = second.reduce((s, t) => s + t.full_score_rate, 0) / second.length
  if (f2 > f1 + 1) dirs.full_score_rate = 'up'
  else if (f2 < f1 - 1) dirs.full_score_rate = 'down'
  return dirs
})

// Random-ish risk bars (stable per session)
const riskBars = computed(() => {
  const count = stats.value?.warning_students?.length || 0
  if (!count) return []
  const seed = count * 7 + 3
  return [0,1,2,3,4,5].map(i => {
    const v = ((seed * (i + 3) * 13) % 60) + 20
    return Math.min(95, v + Math.min(count * 2, 30))
  })
})

// Sparkline helpers
function buildSpark(data, key) {
  if (!data.length) return { line: '', area: '' }
  const values = data.map(d => d[key] || 0)
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = max - min || 1
  const h = 22, padX = 2, padY = 2
  const step = (100 - padX * 2) / Math.max(values.length - 1, 1)

  const pts = values.map((v, i) => {
    const x = (padX + i * step).toFixed(1)
    const y = (h - ((v - min) / range) * (h - padY * 2) - padY).toFixed(1)
    return `${x},${y}`
  })
  const line = pts.join(' ')
  const lastX = (padX + (values.length - 1) * step).toFixed(1)
  const area = `${padX},26 ${pts.join(' ')} ${lastX},26`
  return { line, area }
}

const sparkAvg = computed(() => buildSpark(trends.value, 'predicted_avg_score'))
const sparkFullScore = computed(() => buildSpark(trends.value, 'full_score_rate'))

// ===== Chart Options (dark theme) =====
const chartTextColor = '#94a3b8'
const chartBorderColor = '#1e3a5f'
const chartSplitColor = '#162942'
const chartTooltipBg = '#132238'

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: chartTooltipBg, borderColor: chartBorderColor, textStyle: { color: '#f1f5f9', fontSize: 12 } },
  grid: { left: 38, right: 16, top: 12, bottom: 28 },
  xAxis: {
    type: 'category',
    data: trends.value.map(t => (t.month || '').slice(2) || t.month),
    axisLine: { lineStyle: { color: chartBorderColor } },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontSize: 10 }
  },
  yAxis: {
    type: 'value', min: 0, max: 30,
    splitLine: { lineStyle: { color: chartSplitColor, type: 'dashed' } },
    axisLabel: { color: '#64748b', fontSize: 10 }
  },
  series: [{
    type: 'line',
    data: trends.value.map(t => t.predicted_avg_score),
    smooth: true,
    lineStyle: { color: '#06b6d4', width: 2.5 },
    itemStyle: { color: '#06b6d4' },
    symbol: 'circle', symbolSize: 6,
    areaStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(6,182,212,0.18)' },
          { offset: 1, color: 'rgba(6,182,212,0)' }
        ]
      }
    }
  }]
}))

const radarChartOption = computed(() => {
  const events = stats.value?.event_avgs || []
  return {
    tooltip: { backgroundColor: chartTooltipBg, borderColor: chartBorderColor, textStyle: { color: '#f1f5f9', fontSize: 12 } },
    radar: {
      center: ['50%', '52%'], radius: '65%',
      indicator: events.map(e => ({ name: e.event_name, max: 10 })),
      axisName: { color: chartTextColor, fontSize: 10, padding: [3, 5] },
      splitArea: { areaStyle: { color: ['rgba(6,182,212,0.02)', 'rgba(6,182,212,0.04)'] } },
      splitLine: { lineStyle: { color: chartBorderColor } },
      axisLine: { lineStyle: { color: chartBorderColor } }
    },
    series: [{
      type: 'radar',
      data: [{ value: events.map(e => e.avg_score), name: '均分' }],
      lineStyle: { color: '#06b6d4', width: 2 },
      areaStyle: { color: 'rgba(6,182,212,0.12)' },
      itemStyle: { color: '#06b6d4' },
      symbol: 'circle', symbolSize: 5
    }]
  }
})

const donutChartOption = computed(() => {
  const buckets = stats.value?.score_distribution || []
  const colors = ['#06b6d4', '#0e8fa0', '#10b981', '#f59e0b', '#475569']
  return {
    tooltip: {
      trigger: 'item', formatter: '{b}: {c}人 ({d}%)',
      backgroundColor: chartTooltipBg, borderColor: chartBorderColor, textStyle: { color: '#f1f5f9', fontSize: 12 }
    },
    legend: { bottom: 0, textStyle: { fontSize: 10, color: chartTextColor }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['50%', '76%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#132238', borderWidth: 3 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#f1f5f9' } },
      data: buckets.map((b, i) => ({
        value: b.count, name: b.label, itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  }
})

// AI tips
const aiTips = computed(() => {
  const tips = []
  if (!stats.value) return tips

  const avgDir = trendsDir.value.predicted_avg_score
  const fsDir = trendsDir.value.full_score_rate

  if (avgDir === 'up') {
    tips.push({ type: 'good', text: `整体趋势：<strong style="color:#10b981">上升</strong> — 近6个月均分稳步提升，训练计划执行良好。` })
  } else if (avgDir === 'down') {
    tips.push({ type: 'warn', text: `整体趋势：<strong style="color:#f59e0b">下滑</strong> — 建议排查近期训练强度是否不足或测试标准是否调整。` })
  } else {
    tips.push({ type: 'info', text: `整体趋势：<strong style="color:#06b6d4">平稳</strong> — 均分无明显波动，可按现有节奏继续训练。` })
  }

  // Best & worst events
  const evts = stats.value.event_avgs || []
  const sorted = [...evts].sort((a, b) => b.avg_score - a.avg_score)
  if (sorted.length >= 2) {
    tips.push({ type: 'good', text: `优势项目：<strong style="color:#f1f5f9">${sorted.slice(0, 2).map(e => e.event_name).join('、')}</strong> — 均分较高，继续保持。` })
  }
  if (sorted.length >= 2) {
    const worst = sorted.slice(-2)
    tips.push({ type: 'warn', text: `薄弱项目：<strong style="color:#f59e0b">${worst.map(e => e.event_name).join('、')}</strong> — 全校均分较低，建议纳入重点训练计划。` })
  }

  if (stats.value.risk_classes?.length) {
    const wc = stats.value.risk_classes[0]
    tips.push({ type: 'warn', text: `风险班级：<strong style="color:#f59e0b">${wc.class_name}</strong> — 中考预测均分最低（${wc.predicted_avg_score}分），需重点关注训练质量。` })
  }

  const wCount = stats.value.warning_students?.length || 0
  if (wCount >= 10) {
    tips.push({ type: 'info', text: `行动建议：<strong style="color:#06b6d4">${wCount}名</strong>学生成绩下滑，建议逐一沟通并制定个性化辅导方案。` })
  } else if (wCount === 0) {
    tips.push({ type: 'good', text: `无成绩下滑风险学生，整体训练效果稳定，值得肯定！` })
  } else {
    tips.push({ type: 'info', text: `行动建议：关注<strong style="color:#06b6d4">${wCount}名</strong>下滑风险学生，及时沟通了解原因。` })
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
/* ============================================================
   DESIGN SYSTEM: Deep Navy Cockpit
   ============================================================ */
.cockpit {
  --bg-root:    #0c1929;
  --bg-card:    #132238;
  --bg-hover:   #1a2f4a;
  --cyan:       #06b6d4;
  --cyan-glow:  rgba(6, 182, 212, 0.20);
  --amber:      #f59e0b;
  --emerald:    #10b981;
  --red:        #ef4444;
  --text-a:     #f1f5f9;
  --text-b:     #94a3b8;
  --text-c:     #64748b;
  --border:     #1e3a5f;
  --border-sub: #162942;

  background: var(--bg-root);
  margin: -12px;  /* bleed into Layout padding */
  padding: 20px 24px 40px;
  min-height: calc(100vh - 50px);
  position: relative;
}
/* Subtle noise texture */
.cockpit::before {
  content: '';
  position: absolute; inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0;
}
.cockpit > * { position: relative; z-index: 1; }

/* ===== ① HEADER ===== */
.header {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  background: linear-gradient(180deg, rgba(19,34,56,0.95) 0%, rgba(15,30,51,0.9) 100%);
  border: 1px solid var(--border);
  border-bottom-color: rgba(6,182,212,0.25);
  border-radius: 14px;
  padding: 16px 24px; margin-bottom: 22px;
}
.header-left { display:flex; align-items:center; gap:10px; }
.header-logo { font-size:16px; font-weight:700; color:var(--text-a); letter-spacing:-0.3px; white-space:nowrap; }
.header-badge {
  font-size:9px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
  background: rgba(6,182,212,0.15); color: var(--cyan);
  padding: 3px 10px; border-radius: 20px;
  white-space: nowrap;
}
.header-center { text-align:center; flex:1; min-width:180px; }
.header-greet { font-size:14px; font-weight:600; color:var(--text-a); }
.header-sub  { font-size:11.5px; color:var(--text-b); margin-top:2px; }
.header-right { display:flex; align-items:center; gap:16px; }
.hdr-icon {
  font-size:17px; color:var(--text-b); cursor:pointer; transition:color 0.2s;
  position: relative;
}
.hdr-icon:hover { color: var(--cyan); }
.hdr-icon .dot {
  position:absolute; top:-2px; right:-3px; width:7px; height:7px;
  background:var(--red); border-radius:50%; border:2px solid var(--bg-card);
}
.hdr-avatar {
  width:32px; height:32px; border-radius:50%;
  background: linear-gradient(135deg, var(--cyan), #0891b2);
  display:flex; align-items:center; justify-content:center;
  font-size:13px; font-weight:700; color:#fff; cursor:pointer;
}

/* ===== Section Labels ===== */
.section-label {
  font-size:10.5px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
  color: var(--text-c); margin-bottom:12px;
  display:flex; align-items:center; gap:10px;
}
.section-label::after { content:''; flex:1; height:1px; background:var(--border-sub); }

/* ===== ② KPI CARDS ===== */
.kpi-grid {
  display:grid; grid-template-columns: repeat(4, 1fr);
  gap:14px; margin-bottom:22px;
}
@media (max-width: 1000px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px)  { .kpi-grid { grid-template-columns: 1fr; } }

.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 20px 12px;
  position: relative; overflow: hidden;
  transition: all 0.25s ease;
}
.kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.12);
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.kpi-card::before {
  content:''; position:absolute; top:0; left:50%; transform:translateX(-50%);
  width: calc(100% - 28px); height:3px; border-radius:0 0 3px 3px;
}
.kpi-card.cyan::before    { background: linear-gradient(90deg, transparent, var(--cyan), transparent); }
.kpi-card.amber::before   { background: linear-gradient(90deg, transparent, var(--amber), transparent); }
.kpi-card.emerald::before { background: linear-gradient(90deg, transparent, var(--emerald), transparent); }
.kpi-card.red::before     { background: linear-gradient(90deg, transparent, var(--red), transparent); }

.kpi-label {
  font-size:10px; font-weight:600; letter-spacing:1.2px;
  color: var(--text-c); text-transform:uppercase; margin-bottom:4px;
}
.kpi-row { display:flex; align-items:baseline; gap:6px; margin-bottom:2px; }
.kpi-value {
  font-size:38px; font-weight:800; letter-spacing:-1.5px; line-height:1;
}
.kpi-card.cyan .kpi-value    { color: var(--cyan);    text-shadow: 0 0 24px var(--cyan-glow); }
.kpi-card.amber .kpi-value   { color: var(--amber);   text-shadow: 0 0 24px rgba(245,158,11,0.2); }
.kpi-card.emerald .kpi-value { color: var(--emerald); text-shadow: 0 0 24px rgba(16,185,129,0.2); }
.kpi-card.red .kpi-value     { color: var(--red);     text-shadow: 0 0 24px rgba(239,68,68,0.2); }

.kpi-unit { font-size:13px; font-weight:500; color:var(--text-c); }
.kpi-delta { font-size:12px; font-weight:700; margin-left:2px; }
.kpi-delta.up   { color: var(--emerald); }
.kpi-delta.down { color: var(--red); }
.kpi-delta.flat { color: var(--text-c); }
.kpi-arrow { font-size:11px; }

.kpi-spark { width:100%; height:28px; margin-top:6px; display:block; }
.kpi-sub  { margin-top:2px; font-size:10px; color:var(--text-c); }

/* Sparkline gradient definitions */
.kpi-spark :deep(linearGradient) {}

/* ===== ③ STATS BAR ===== */
.stats-bar {
  display:flex; align-items:center; flex-wrap:wrap; gap:0;
  background: var(--bg-card); border: 1px solid var(--border-sub);
  border-radius: 10px; padding: 8px 4px; margin-bottom:24px;
}
.stat-item {
  display:flex; align-items:center; gap:7px; padding:6px 16px;
  flex:1; min-width:100px; justify-content:center;
}
.stat-icon { font-size:15px; flex-shrink:0; opacity:0.8; }
.stat-label { font-size:11px; color:var(--text-c); white-space:nowrap; }
.stat-num { font-size:16px; font-weight:700; color:var(--text-a); }
.stat-divider { width:1px; height:20px; background:var(--border-sub); flex-shrink:0; }
@media (max-width: 768px) { .stat-divider { display:none; } }

/* ===== ④ CHARTS ===== */
.charts-grid {
  display:grid; grid-template-columns: repeat(3, 1fr);
  gap:14px; margin-bottom:22px;
}
@media (max-width: 1000px) { .charts-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 650px)  { .charts-grid { grid-template-columns: 1fr; } }

.chart-card {
  background: var(--bg-card); border: 1px solid var(--border-sub);
  border-radius: 14px; padding: 16px 18px 10px;
  transition: border-color 0.2s;
}
.chart-card:hover { border-color: var(--border); }
.chart-title  { font-size:12.5px; font-weight:600; color:var(--text-a); margin-bottom:2px; }
.chart-sub    { font-weight:400; font-size:10px; color:var(--text-c); margin-left:6px; }
.chart-empty { height:200px; display:flex; align-items:center; justify-content:center; color:var(--text-c); font-size:13px; }

/* ===== ⑤ BOTTOM ===== */
.bottom-grid {
  display:grid; grid-template-columns: 1fr 1fr;
  gap:14px; margin-bottom:16px;
}
@media (max-width: 768px) { .bottom-grid { grid-template-columns: 1fr; } }

.risk-card, .ai-card {
  background: var(--bg-card); border: 1px solid var(--border-sub);
  border-radius: 14px; overflow:hidden;
}
.risk-hd, .ai-hd {
  padding:13px 20px; border-bottom:1px solid var(--border-sub);
  font-size:13px; font-weight:600; display:flex; align-items:center; justify-content:space-between;
}
.risk-badge, .ai-badge {
  padding:2px 10px; border-radius:20px; font-size:10px; font-weight:700;
}
.risk-badge.red  { background: rgba(239,68,68,0.15); color:var(--red); }
.risk-badge.good { background: rgba(16,185,129,0.15); color:var(--emerald); }
.ai-badge { background: rgba(6,182,212,0.12); color:var(--cyan); }

.risk-list { padding:4px 0; }
.risk-row {
  display:flex; align-items:center; gap:10px;
  padding:10px 20px; transition:background 0.15s;
}
.risk-row:hover { background: var(--bg-hover); }
.risk-rank {
  width:22px; text-align:center; font-size:11px; font-weight:700;
  color:var(--text-c); flex-shrink:0;
}
.risk-rank.top3 { color:var(--amber); }
.risk-info { flex:1; min-width:0; }
.risk-name { font-size:12.5px; font-weight:600; color:var(--text-a); }
.risk-meta { font-size:10px; color:var(--text-c); margin-top:1px; }
.risk-decline { font-size:13px; font-weight:700; color:var(--red); flex-shrink:0; }
.risk-detail { font-size:10px; color:var(--text-c); flex-shrink:0; width:38px; text-align:right; }
.risk-empty { padding:32px 20px; text-align:center; color:var(--text-c); font-size:13px; }

/* AI Card */
.ai-body { padding:14px 20px 18px; }
.ai-item {
  display:flex; align-items:flex-start; gap:10px;
  padding:9px 0; font-size:12.5px; color:var(--text-b); line-height:1.55;
}
.ai-item + .ai-item { border-top:1px solid var(--border-sub); }
.ai-dot { width:8px; height:8px; border-radius:50%; margin-top:5px; flex-shrink:0; }
.ai-dot.good  { background:var(--emerald); box-shadow: 0 0 6px rgba(16,185,129,0.4); }
.ai-dot.warn  { background:var(--amber);   box-shadow: 0 0 6px rgba(245,158,11,0.4); }
.ai-dot.info  { background:var(--cyan);    box-shadow: 0 0 6px rgba(6,182,212,0.4); }

/* Loading pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
