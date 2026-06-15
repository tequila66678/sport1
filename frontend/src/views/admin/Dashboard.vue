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
        <div class="header-sub">{{ schoolName }} ｜ 本期中考学生：{{ cohort }}</div>
      </div>
      <div class="header-right">
        <!-- Quick Nav -->
        <nav class="quick-nav">
          <router-link to="/admin/score-entry" class="qn-link">📝 录入</router-link>
          <router-link to="/admin/students" class="qn-link">👥 学生</router-link>
          <router-link to="/admin/statistics" class="qn-link">📈 统计</router-link>
          <router-link v-if="adminInfo?.role !== 'teacher'" to="/admin/settings" class="qn-link">⚙️ 设置</router-link>
        </nav>
        <span class="hdr-icon" title="通知">🔔<span class="dot"></span></span>
        <span class="hdr-avatar">{{ avatarChar }}</span>
      </div>
    </header>

    <!-- ===== ② KPI CARDS ===== -->
    <div class="section-label">核心决策指标</div>
    <section class="kpi-grid" v-if="stats">
      <div class="kpi-card cyan">
        <div class="kpi-label">预计中考满分率</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ stats.full_score_rate ?? '--' }}</span>
          <span class="kpi-unit">%</span>
          <span class="kpi-delta" :class="trendsDir.full_score_rate">
            <span class="kpi-arrow">{{ trendsDir.full_score_rate === 'up' ? '↑' : trendsDir.full_score_rate === 'down' ? '↓' : '→' }}</span>
          </span>
        </div>
        <div class="kpi-sub">中考总分=30时为满分</div>
      </div>
      <div class="kpi-card amber">
        <div class="kpi-label">预测中考均分</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ stats.predicted_avg_score ?? '--' }}</span>
          <span class="kpi-unit">/30</span>
          <span class="kpi-delta" :class="trendsDir.predicted_avg_score">
            <span class="kpi-arrow">{{ trendsDir.predicted_avg_score === 'up' ? '↑' : trendsDir.predicted_avg_score === 'down' ? '↓' : '→' }}</span>
          </span>
        </div>
        <div class="kpi-sub">长跑(必考)+最优2项</div>
      </div>
      <div class="kpi-card emerald">
        <div class="kpi-label">测试参与率</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ participationRate }}</span>
          <span class="kpi-unit">%</span>
        </div>
        <div class="kpi-sub">{{ stats.participants ?? 0 }} / {{ stats.total_students ?? 0 }} 人</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-label">下滑风险学生</div>
        <div class="kpi-row">
          <span class="kpi-value">{{ stats.warning_students?.length ?? 0 }}</span>
          <span class="kpi-unit">人</span>
        </div>
        <div class="kpi-sub">{{ stats.warning_students?.length ? '近两次成绩下滑≥2分' : '✅ 暂无下滑风险' }}</div>
      </div>
    </section>

    <div v-if="!stats" class="loading-box" style="display:flex;gap:12px;margin-bottom:22px">
      <div v-for="i in 4" :key="i" style="flex:1;height:120px;background:#132238;border-radius:14px;border:1px solid #1e3a5f;animation:pulse 1.5s infinite" />
    </div>

    <!-- ===== ③ SECONDARY STATS ===== -->
    <section class="stats-bar" v-if="stats">
      <div class="stat-item">
        <span class="stat-icon">👥</span><span class="stat-label">考生人数</span><span class="stat-num">{{ stats.total_students?.toLocaleString() ?? '--' }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">🏃</span><span class="stat-label">本月训练</span><span class="stat-num">{{ (stats.training_count_this_month || 0).toLocaleString() }}次</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">⚠️</span><span class="stat-label">风险班级</span><span class="stat-num">{{ stats.risk_classes?.length ?? 0 }}个</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-icon">📊</span><span class="stat-label">班级总数</span><span class="stat-num">{{ stats.total_classes ?? '--' }}个</span>
      </div>
    </section>

    <!-- ===== ④ CHARTS ===== -->
    <div class="section-label">多维数据分析</div>
    <section class="charts-grid" v-if="stats">
      <div class="chart-card">
        <div class="chart-title">📈 均分趋势<span class="chart-sub">近6个月</span></div>
        <v-chart :option="trendChartOption" autoresize style="height:240px" v-if="trends.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🕸 项目能力雷达<span class="chart-sub">各项目均分</span></div>
        <v-chart :option="radarChartOption" autoresize style="height:240px" v-if="stats?.event_avgs?.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🍩 分数分布<span class="chart-sub">中考总分分档</span></div>
        <v-chart :option="donutChartOption" autoresize style="height:240px" v-if="stats?.score_distribution?.length" />
        <div v-else class="chart-empty">暂无数据</div>
      </div>
    </section>

    <!-- ===== ⑤ BOTTOM ===== -->
    <section class="bottom-grid" v-if="stats">
      <div class="risk-card">
        <div class="risk-hd">
          <span>🚨 下滑风险 TOP5</span>
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
          </div>
        </div>
        <div v-else class="risk-empty">✅ 暂无下滑风险</div>
      </div>
      <div class="ai-card">
        <div class="ai-hd">
          <span>💡 AI 分析</span>
          <span class="ai-badge">实时</span>
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

// ===== Dynamic Cohort =====
// 体育中考每年4月中旬考完，5月起自动切换到下一届
const now = new Date()
const cohortYear = now.getMonth() >= 4 ? now.getFullYear() + 1 : now.getFullYear()  // month>=4 means May+
const cohort = ref(`${cohortYear}届`)

// ===== State =====
const stats = ref(null)
const trends = ref([])
const adminInfo = ref(null)

onMounted(() => {
  try {
    adminInfo.value = JSON.parse(localStorage.getItem('admin_info') || '{}')
  } catch {}
  loadData()
})

// ===== Computed =====
const greeting = computed(() => {
  const h = now.getHours()
  if (h < 6) return '🌙 夜深了，船长'
  if (h < 9) return '🌅 早上好，船长'
  if (h < 12) return '☀️ 上午好，船长'
  if (h < 14) return '🌤 中午好，船长'
  if (h < 18) return '👋 下午好，船长'
  return '🌆 晚上好，船长'
})

const schoolName = computed(() => {
  return adminInfo.value?.school_name || '体育成绩管理系统'
})

const avatarChar = computed(() => {
  return (adminInfo.value?.display_name || '管')[0]
})

const participationRate = computed(() => {
  if (!stats.value) return '--'
  const { participants, total_students } = stats.value
  if (!total_students) return '0'
  return Math.round(participants / total_students * 100)
})

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

// ===== Chart Options =====
const chartTooltipBg = '#132238'
const chartBorderColor = '#1e3a5f'
const chartSplitColor = '#162942'

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: chartTooltipBg, borderColor: chartBorderColor, textStyle: { color: '#f1f5f9', fontSize: 12 } },
  grid: { left: 38, right: 16, top: 8, bottom: 24 },
  xAxis: {
    type: 'category',
    data: trends.value.map(t => (t.month || '').slice(2)),
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
    type: 'line', data: trends.value.map(t => t.predicted_avg_score),
    smooth: true, lineStyle: { color: '#06b6d4', width: 2.5 },
    itemStyle: { color: '#06b6d4' }, symbol: 'circle', symbolSize: 6,
    areaStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(6,182,212,0.18)' }, { offset: 1, color: 'rgba(6,182,212,0)' }] }
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
      axisName: { color: '#94a3b8', fontSize: 10, padding: [3, 5] },
      splitArea: { areaStyle: { color: ['rgba(6,182,212,0.02)', 'rgba(6,182,212,0.04)'] } },
      splitLine: { lineStyle: { color: chartBorderColor } },
      axisLine: { lineStyle: { color: chartBorderColor } }
    },
    series: [{
      type: 'radar', data: [{ value: events.map(e => e.avg_score), name: '均分' }],
      lineStyle: { color: '#06b6d4', width: 2 }, areaStyle: { color: 'rgba(6,182,212,0.12)' },
      itemStyle: { color: '#06b6d4' }, symbol: 'circle', symbolSize: 5
    }]
  }
})

const donutChartOption = computed(() => {
  const buckets = stats.value?.score_distribution || []
  const colors = ['#06b6d4', '#0e8fa0', '#10b981', '#f59e0b', '#475569']
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)', backgroundColor: chartTooltipBg, borderColor: chartBorderColor, textStyle: { color: '#f1f5f9', fontSize: 12 } },
    legend: { bottom: 0, textStyle: { fontSize: 10, color: '#94a3b8' }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie', radius: ['50%', '76%'], center: ['50%', '46%'],
      avoidLabelOverlap: false, itemStyle: { borderRadius: 4, borderColor: '#132238', borderWidth: 3 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#f1f5f9' } },
      data: buckets.map((b, i) => ({ value: b.count, name: b.label, itemStyle: { color: colors[i % colors.length] } }))
    }]
  }
})

// ===== AI Tips =====
const aiTips = computed(() => {
  const tips = []
  if (!stats.value) return tips
  const avgDir = trendsDir.value.predicted_avg_score
  const fsDir = trendsDir.value.full_score_rate

  if (avgDir === 'up') tips.push({ type: 'good', text: `均分趋势：<strong style="color:#10b981">持续上升</strong>，训练计划执行良好。` })
  else if (avgDir === 'down') tips.push({ type: 'warn', text: `均分趋势：<strong style="color:#f59e0b">下滑</strong>，建议排查训练强度是否不足。` })
  else tips.push({ type: 'info', text: `均分趋势：<strong style="color:#06b6d4">平稳</strong>，按现有节奏继续训练。` })

  const evts = stats.value.event_avgs || []
  const sorted = [...evts].sort((a, b) => b.avg_score - a.avg_score)
  if (sorted.length >= 2) {
    tips.push({ type: 'good', text: `优势：<strong style="color:#f1f5f9">${sorted.slice(0, 2).map(e => e.event_name).join('、')}</strong> 均分领先。` })
    const worst = sorted.slice(-2)
    tips.push({ type: 'warn', text: `短板：<strong style="color:#f59e0b">${worst.map(e => e.event_name).join('、')}</strong> 需重点加强。` })
  }

  if (stats.value.risk_classes?.length) {
    const wc = stats.value.risk_classes[0]
    tips.push({ type: 'warn', text: `风险班级：<strong style="color:#f59e0b">${wc.class_name}</strong> 预测均分仅${wc.predicted_avg_score}分。` })
  }

  const wCount = stats.value.warning_students?.length || 0
  if (wCount === 0) tips.push({ type: 'good', text: `无下滑风险学生，整体训练效果稳定！` })
  else tips.push({ type: 'info', text: `建议对 <strong style="color:#06b6d4">${wCount}名</strong> 下滑学生进行个性化辅导。` })

  return tips
})

// ===== Data Fetching =====
async function loadData() {
  const params = { grade: cohort.value }
  try {
    const [statsRes, trendsRes] = await Promise.all([
      api.get('/scores/school-stats', { params }),
      api.get('/scores/trends', { params })
    ])
    stats.value = statsRes.data
    trends.value = trendsRes.data || []
  } catch (e) {
    console.error('Dashboard load error:', e)
  }
}
</script>

<style scoped>
/* ===== DESIGN TOKENS ===== */
.cockpit {
  --bg-root: #0c1929; --bg-card: #132238; --bg-hover: #1a2f4a;
  --cyan: #06b6d4; --cyan-glow: rgba(6,182,212,0.20);
  --amber: #f59e0b; --emerald: #10b981; --red: #ef4444;
  --text-a: #f1f5f9; --text-b: #94a3b8; --text-c: #64748b;
  --border: #1e3a5f; --border-sub: #162942;
  background: var(--bg-root);
  margin: -12px; padding: 20px 24px 40px;
  min-height: calc(100vh - 50px);
  position: relative;
}
.cockpit::before {
  content: ''; position: absolute; inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0;
}
.cockpit > * { position: relative; z-index: 1; }

/* ===== HEADER ===== */
.header {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  background: linear-gradient(180deg, rgba(19,34,56,0.95) 0%, rgba(15,30,51,0.9) 100%);
  border: 1px solid var(--border); border-bottom-color: rgba(6,182,212,0.25);
  border-radius: 14px; padding: 14px 20px; margin-bottom: 20px;
}
.header-left { display:flex; align-items:center; gap:10px; }
.header-logo { font-size:16px; font-weight:700; color:var(--text-a); letter-spacing:-0.3px; white-space:nowrap; }
.header-badge { font-size:9px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; background: rgba(6,182,212,0.15); color: var(--cyan); padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
.header-center { text-align:center; flex:1; min-width:160px; }
.header-greet { font-size:14px; font-weight:600; color:var(--text-a); }
.header-sub  { font-size:11.5px; color:var(--text-b); margin-top:2px; }
.header-right { display:flex; align-items:center; gap:14px; }

/* Quick nav */
.quick-nav { display:flex; align-items:center; gap:6px; }
.qn-link {
  font-size:11px; font-weight:600; color:var(--text-b); text-decoration:none;
  padding:5px 10px; border-radius:8px; transition:all 0.2s;
  border:1px solid transparent; white-space:nowrap;
}
.qn-link:hover { color:var(--cyan); border-color:var(--border); background:rgba(6,182,212,0.06); }

.hdr-icon { font-size:17px; color:var(--text-b); cursor:pointer; transition:color 0.2s; position:relative; }
.hdr-icon:hover { color: var(--cyan); }
.hdr-icon .dot { position:absolute; top:-2px; right:-3px; width:7px; height:7px; background:var(--red); border-radius:50%; border:2px solid var(--bg-card); }
.hdr-avatar { width:32px; height:32px; border-radius:50%; background: linear-gradient(135deg, var(--cyan), #0891b2); display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; color:#fff; cursor:pointer; }

/* ===== SECTION LABEL ===== */
.section-label { font-size:10.5px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--text-c); margin-bottom:10px; display:flex; align-items:center; gap:10px; }
.section-label::after { content:''; flex:1; height:1px; background:var(--border-sub); }

/* ===== KPI ===== */
.kpi-grid { display:grid; grid-template-columns: repeat(4, 1fr); gap:14px; margin-bottom:20px; }
@media (max-width: 1000px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px)  { .kpi-grid { grid-template-columns: 1fr; } }

.kpi-card { background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:18px 20px 12px; position:relative; overflow:hidden; transition:all 0.25s ease; }
.kpi-card:hover { transform:translateY(-2px); border-color:rgba(255,255,255,0.12); box-shadow:0 8px 32px rgba(0,0,0,0.35); }
.kpi-card::before { content:''; position:absolute; top:0; left:50%; transform:translateX(-50%); width:calc(100% - 28px); height:3px; border-radius:0 0 3px 3px; }
.kpi-card.cyan::before    { background: linear-gradient(90deg, transparent, var(--cyan), transparent); }
.kpi-card.amber::before   { background: linear-gradient(90deg, transparent, var(--amber), transparent); }
.kpi-card.emerald::before { background: linear-gradient(90deg, transparent, var(--emerald), transparent); }
.kpi-card.red::before     { background: linear-gradient(90deg, transparent, var(--red), transparent); }

.kpi-label { font-size:10px; font-weight:600; letter-spacing:1.2px; color:var(--text-c); text-transform:uppercase; margin-bottom:4px; }
.kpi-row { display:flex; align-items:baseline; gap:6px; margin-bottom:2px; }
.kpi-value { font-size:38px; font-weight:800; letter-spacing:-1.5px; line-height:1; }
.kpi-card.cyan .kpi-value    { color:var(--cyan);    text-shadow:0 0 24px var(--cyan-glow); }
.kpi-card.amber .kpi-value   { color:var(--amber);   text-shadow:0 0 24px rgba(245,158,11,0.2); }
.kpi-card.emerald .kpi-value { color:var(--emerald); text-shadow:0 0 24px rgba(16,185,129,0.2); }
.kpi-card.red .kpi-value     { color:var(--red);     text-shadow:0 0 24px rgba(239,68,68,0.2); }
.kpi-unit { font-size:13px; font-weight:500; color:var(--text-c); }
.kpi-delta { font-size:12px; font-weight:700; margin-left:2px; }
.kpi-delta.up   { color:var(--emerald); }
.kpi-delta.down { color:var(--red); }
.kpi-delta.flat { color:var(--text-c); }
.kpi-arrow { font-size:11px; }
.kpi-sub  { margin-top:2px; font-size:10px; color:var(--text-c); }

/* ===== STATS BAR ===== */
.stats-bar { display:flex; align-items:center; flex-wrap:wrap; background:var(--bg-card); border:1px solid var(--border-sub); border-radius:10px; padding:8px 4px; margin-bottom:22px; }
.stat-item { display:flex; align-items:center; gap:7px; padding:6px 16px; flex:1; min-width:80px; justify-content:center; }
.stat-icon { font-size:14px; flex-shrink:0; opacity:0.8; }
.stat-label { font-size:10.5px; color:var(--text-c); white-space:nowrap; }
.stat-num { font-size:15px; font-weight:700; color:var(--text-a); }
.stat-divider { width:1px; height:18px; background:var(--border-sub); flex-shrink:0; }
@media (max-width: 600px) { .stat-divider { display:none; } }

/* ===== CHARTS ===== */
.charts-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-bottom:20px; }
@media (max-width: 1000px) { .charts-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 650px)  { .charts-grid { grid-template-columns: 1fr; } }
.chart-card { background:var(--bg-card); border:1px solid var(--border-sub); border-radius:14px; padding:14px 16px 8px; transition:border-color 0.2s; }
.chart-card:hover { border-color:var(--border); }
.chart-title  { font-size:12.5px; font-weight:600; color:var(--text-a); margin-bottom:2px; }
.chart-sub    { font-weight:400; font-size:10px; color:var(--text-c); margin-left:6px; }
.chart-empty { height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-c); font-size:13px; }

/* ===== BOTTOM ===== */
.bottom-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
@media (max-width: 768px) { .bottom-grid { grid-template-columns:1fr; } }
.risk-card, .ai-card { background:var(--bg-card); border:1px solid var(--border-sub); border-radius:14px; overflow:hidden; }
.risk-hd, .ai-hd { padding:12px 18px; border-bottom:1px solid var(--border-sub); font-size:13px; font-weight:600; display:flex; align-items:center; justify-content:space-between; }
.risk-badge, .ai-badge { padding:2px 10px; border-radius:20px; font-size:10px; font-weight:700; }
.risk-badge.red  { background:rgba(239,68,68,0.15); color:var(--red); }
.risk-badge.good { background:rgba(16,185,129,0.15); color:var(--emerald); }
.ai-badge { background:rgba(6,182,212,0.12); color:var(--cyan); }
.risk-list { padding:4px 0; }
.risk-row { display:flex; align-items:center; gap:10px; padding:10px 18px; transition:background 0.15s; }
.risk-row:hover { background:var(--bg-hover); }
.risk-rank { width:20px; text-align:center; font-size:11px; font-weight:700; color:var(--text-c); flex-shrink:0; }
.risk-rank.top3 { color:var(--amber); }
.risk-info { flex:1; min-width:0; }
.risk-name { font-size:12.5px; font-weight:600; color:var(--text-a); }
.risk-meta { font-size:10px; color:var(--text-c); margin-top:1px; }
.risk-decline { font-size:13px; font-weight:700; color:var(--red); flex-shrink:0; }
.risk-empty { padding:32px 18px; text-align:center; color:var(--text-c); font-size:13px; }
.ai-body { padding:12px 18px 16px; }
.ai-item { display:flex; align-items:flex-start; gap:10px; padding:8px 0; font-size:12px; color:var(--text-b); line-height:1.55; }
.ai-item + .ai-item { border-top:1px solid var(--border-sub); }
.ai-dot { width:8px; height:8px; border-radius:50%; margin-top:4px; flex-shrink:0; }
.ai-dot.good  { background:var(--emerald); box-shadow:0 0 6px rgba(16,185,129,0.4); }
.ai-dot.warn  { background:var(--amber);   box-shadow:0 0 6px rgba(245,158,11,0.4); }
.ai-dot.info  { background:var(--cyan);    box-shadow:0 0 6px rgba(6,182,212,0.4); }

@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
</style>
