<template>
  <div class="stats-page">
    <el-button text @click="$router.push('/admin/dashboard')" class="back-btn">← 返回仪表盘</el-button>
    <h3 style="margin:8px 0 12px">统计分析</h3>
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="年级对比" name="grade">
        <div class="ctx-note"><span class="ctx-dot"></span> 近30天各项目最好成绩 · 中考总分 = 长跑(必考) + 其余最好2项</div>
        <el-select v-model="gradeEventIds" multiple placeholder="选择项目（可选）" @change="loadGradeStats" style="width:100%;margin-bottom:12px" size="default" collapse-tags>
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>

        <div v-if="gradeStatsList && gradeStatsList.length">
          <div v-for="g in gradeStatsList" :key="g.grade" class="grade-block">
            <div class="grade-label"><span class="grade-dot"></span>{{ g.grade }}</div>

            <div class="kpi-grid">
              <div class="kpi-card indigo">
                <div class="kpi-label">预测中考均分</div>
                <div class="kpi-value-row"><span class="kpi-value">{{ g.predicted_avg_score ?? '--' }}</span><span class="kpi-unit">/ 30</span></div>
                <div class="kpi-sub">满分率 {{ g.full_score_rate }}% · {{ g.participants }}人参与</div>
              </div>
              <div class="kpi-card gold">
                <div class="kpi-label">🏆 预计中考满分率</div>
                <div class="kpi-value-row"><span class="kpi-value">{{ g.full_score_rate }}</span><span class="kpi-unit">%</span></div>
                <div class="kpi-sub">{{ g.score_distribution?.[0]?.count ?? 0 }}人满分</div>
              </div>
              <div class="kpi-card amber">
                <div class="kpi-label">⚠ 下滑风险学生</div>
                <div class="kpi-value-row"><span class="kpi-value">{{ g.warning_students?.length ?? 0 }}</span><span class="kpi-unit">人</span></div>
                <div class="kpi-sub">占比 {{ g.participants ? (g.warning_students?.length / g.participants * 100).toFixed(1) : 0 }}%</div>
              </div>
            </div>

            <div class="risk-grid" v-if="g.risk_events?.length || g.risk_classes?.length" style="margin-top:12px">
              <div class="risk-card" v-if="g.risk_events?.length">
                <div class="risk-hd">风险项目</div>
                <div class="risk-list">
                  <div class="risk-row" v-for="(e, i) in g.risk_events" :key="e.event_id">
                    <span class="risk-rank">{{ i + 1 }}</span>
                    <div class="risk-info"><div class="risk-name">{{ e.event_name }}</div></div>
                    <span :class="['risk-value', e.avg_score < 6 ? 'low' : 'mid']">{{ e.avg_score }}</span>
                  </div>
                </div>
              </div>
              <div class="risk-card" v-if="g.risk_classes?.length">
                <div class="risk-hd">风险班级</div>
                <div class="risk-list">
                  <div class="risk-row" v-for="(c, i) in g.risk_classes" :key="c.class_id">
                    <span class="risk-rank">{{ i + 1 }}</span>
                    <div class="risk-info"><div class="risk-name">{{ c.class_name }}</div></div>
                    <span class="risk-value" :class="c.predicted_avg_score < 18 ? 'low' : 'mid'">{{ c.predicted_avg_score }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-hint">暂未选择或该年级没有数据</div>
      </el-tab-pane>

      <!-- ============================================
           TAB: 班级详情
           ============================================ -->
      <el-tab-pane label="班级详情" name="class">
        <el-select v-model="statsClassId" placeholder="选择班级" @change="loadClassStats" style="width:100%;margin-bottom:8px" size="default">
          <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
        </el-select>
        <el-select v-model="statsEventIds" multiple placeholder="选择项目（可选）" @change="loadClassStats" style="width:100%;margin-bottom:8px" size="default" collapse-tags>
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-button type="primary" size="small" @click="showExport = true" style="margin-bottom:12px">导出班级成绩</el-button>

        <div v-if="classStats">
          <div class="ctx-note"><span class="ctx-dot"></span> {{ classStats.class_name }} · {{ classStats.total_students }}人在校 · {{ classStats.participants }}人参与</div>

          <div class="section-label">班级核心指标</div>
          <div class="kpi-grid">
            <div class="kpi-card indigo">
              <div class="kpi-label">预测中考均分</div>
              <div class="kpi-value-row"><span class="kpi-value">{{ classStats.predicted_avg_score ?? '--' }}</span><span class="kpi-unit">/ 30</span></div>
              <div class="kpi-sub">班级均分</div>
            </div>
            <div class="kpi-card gold">
              <div class="kpi-label">🏆 预计中考满分率</div>
              <div class="kpi-value-row"><span class="kpi-value">{{ classStats.full_score_rate }}</span><span class="kpi-unit">%</span></div>
              <div class="kpi-sub">{{ classStats.score_distribution?.[0]?.count ?? 0 }}人满分</div>
            </div>
            <div class="kpi-card amber">
              <div class="kpi-label">⚠ 下滑风险学生</div>
              <div class="kpi-value-row"><span class="kpi-value">{{ classStats.warning_students?.length ?? 0 }}</span><span class="kpi-unit">人</span></div>
              <div class="kpi-sub">需重点关注的个体</div>
            </div>
          </div>

          <div class="risk-grid" style="margin-top:8px">
            <div class="risk-card" v-if="classStats.risk_events?.length">
              <div class="risk-hd">薄弱项目</div>
              <div class="risk-list">
                <div class="risk-row" v-for="(e, i) in classStats.risk_events" :key="e.event_id">
                  <span class="risk-rank" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
                  <div class="risk-info"><div class="risk-name">{{ e.event_name }}</div></div>
                  <span :class="['risk-value', e.avg_score < 6 ? 'low' : 'mid']">{{ e.avg_score }}</span>
                </div>
              </div>
            </div>
            <div class="risk-card" v-if="classStats.warning_students?.length">
              <div class="risk-hd">下滑学生</div>
              <div class="risk-list">
                <div class="student-risk-row" v-for="w in classStats.warning_students" :key="w.student_no">
                  <div :class="['student-avatar-sm', w.student_gender === 'M' ? 'male' : 'female']">{{ w.student_name[0] }}</div>
                  <div class="risk-info">
                    <div class="risk-name">{{ w.student_name }}</div>
                    <div class="risk-meta">{{ w.event_name }}：{{ w.prev_score }} → <span class="score-drop">{{ w.curr_score }}</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Student score matrix table -->
          <div v-if="classScoreTable" class="section-label" style="margin-top:16px">学生成绩明细</div>
          <div v-if="classScoreTable" class="score-table-wrap">
            <el-table :data="classScoreTable.students" stripe size="small" style="width:100%" border>
              <el-table-column prop="student_id" label="学号" width="100" fixed />
              <el-table-column prop="student_name" label="姓名" width="80" fixed />
              <el-table-column v-for="evt in classScoreTable.events" :key="evt.id" :label="evt.name" min-width="100" align="center">
                <template #default="{ row }">
                  <span v-if="row.scores[evt.id]" class="cell-score" :class="{ 'cell-best': row.scores[evt.id]?.earned_score >= 9 }">
                    {{ row.scores[evt.id]?.earned_score ?? '-' }}
                  </span>
                  <span v-else class="cell-empty">-</span>
                </template>
              </el-table-column>
            </el-table>
            <div class="table-hint">* 优先取近30天该项目最好成绩，若30天内未测试则取最近一次成绩</div>
          </div>
        </div>
        <div v-else class="empty-hint">请选择班级</div>
      </el-tab-pane>

      <!-- ============================================
           TAB: 个人追踪
           ============================================ -->
      <el-tab-pane label="个人追踪" name="student">
        <el-input v-model="studentSearch" placeholder="输入学号或姓名搜索" @change="searchStudent" style="margin-bottom:8px" clearable />
        <el-select v-model="studentEventIds" multiple placeholder="选择项目（可选）" @change="reloadStudentStats" style="width:100%;margin-bottom:8px" collapse-tags>
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>

        <div v-if="studentStats">
          <div class="student-hd">
            <div class="student-avatar-lg">{{ studentStats.student.name[0] }}</div>
            <div>
              <div class="student-name-lg">{{ studentStats.student.name }}</div>
              <div class="student-meta-lg">{{ studentStats.student.gender === 'M' ? '男' : '女' }} · {{ studentStats.student.student_id }} · {{ studentStats.student.class_grade }}{{ studentStats.student.class_name }}</div>
            </div>
          </div>
          <el-button type="primary" size="small" @click="showExport = true" style="margin-bottom:12px">导出个人成绩</el-button>

          <div class="rec-card">
            <div class="rec-title">🏆 中考推荐（按得分排序）</div>
            <div class="rec-item" v-for="(r, i) in studentStats.recommended_events" :key="r.rank"
                 :class="i === 0 ? 'gold' : i === 1 ? 'silver' : 'bronze'">
              <span class="rec-medal">{{ r.medal }}</span>
              <span class="rec-event">{{ r.event_name }}</span>
              <span class="rec-score">{{ r.score }} 分</span>
            </div>
          </div>

          <v-chart v-if="chartOption" :option="chartOption" style="height:320px;margin-top:12px" autoresize />

          <el-card v-if="studentStats.scores_by_event" style="margin-top:12px">
            <template #header>成绩记录</template>
            <div v-for="(scoreList, eventName) in studentStats.scores_by_event" :key="eventName" style="margin:6px 0">
              <strong>{{ eventName }}</strong>:
              <span v-for="sc in scoreList" :key="sc.id" style="margin-left:6px;font-size:13px">
                {{ sc.raw_value }}（{{ sc.earned_score }}分）{{ sc.test_date }}
                <el-button text type="danger" size="small" @click="deleteScore(sc.id)" style="padding:0;margin:0;font-size:11px">×</el-button>
              </span>
            </div>
          </el-card>
        </div>
        <div v-else class="empty-hint">请搜索学生姓名或学号</div>
      </el-tab-pane>
    </el-tabs>

    <ExportDialog v-model="showExport" :classes="classes" :events="events" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'
import ExportDialog from '../../components/ExportDialog.vue'
import VChart from 'vue-echarts'
import 'echarts'

const activeTab = ref('grade')
const classes = ref([])
const events = ref([])
const showExport = ref(false)

// School stats

// Grade stats
const gradeEventIds = ref([])
const gradeStatsList = ref(null)
const gradeOptions = computed(() => [...new Set(classes.value.map(c => c.grade))].sort())

// Class stats
const statsClassId = ref(null)
const statsEventIds = ref([])
const classStats = ref(null)
const classScoreTable = ref(null)

// Student stats
const studentSearch = ref('')
const studentEventIds = ref([])
const studentStats = ref(null)
let currentStudentId = null

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([api.get('/events/classes'), api.get('/events')])
  classes.value = cRes.data.map(c => ({ ...c, label: `${c.grade}${c.name}` }))
  events.value = eRes.data
})

function onTabChange(tab) {
  if (tab === 'grade') loadGradeStats()
}

async function loadGradeStats() {
  const params = {}
  if (gradeEventIds.value.length) params.event_ids = gradeEventIds.value.join(',')
  const res = await api.get('/scores/grade-stats', { params })
  gradeStatsList.value = res.data
}

async function loadClassStats() {
  if (!statsClassId.value) { classStats.value = null; classScoreTable.value = null; return }
  const params = { class_id: statsClassId.value }
  if (statsEventIds.value.length) params.event_ids = statsEventIds.value.join(',')
  const [statsRes, tableRes] = await Promise.all([
    api.get('/scores/class-stats', { params }),
    api.get('/scores/class-score-table', { params: { class_id: statsClassId.value } })
  ])
  classStats.value = statsRes.data
  classScoreTable.value = tableRes.data
}

async function searchStudent() {
  if (!studentSearch.value) return
  const res = await api.get('/students', { params: { search: studentSearch.value, page_size: 10 } })
  if (res.data.length > 0) { currentStudentId = res.data[0].id; loadStudentStats() }
}

async function loadStudentStats() {
  const params = {}
  if (studentEventIds.value.length) params.event_ids = studentEventIds.value.join(',')
  const res = await api.get(`/scores/student-stats/${currentStudentId}`, { params })
  studentStats.value = res.data
}

async function deleteScore(scoreId) {
  try { await ElMessageBox.confirm('确定删除这条成绩记录？', '确认删除', { type: 'warning' }) } catch { return }
  await api.delete(`/scores/${scoreId}`)
  ElMessage.success('已删除')
  loadStudentStats()
}

function reloadStudentStats() { if (currentStudentId) loadStudentStats() }

// ===== Trend Charts =====

// ===== Student trend chart (unchanged logic) =====
const chartOption = computed(() => {
  if (!studentStats.value?.scores_by_event) return null
  const data = studentStats.value.scores_by_event
  const eventNames = Object.keys(data).filter(k => {
    return data[k].length >= 2 && data[k].some(s => s.numeric_value != null)
  })
  if (!eventNames.length) return null

  const allDates = new Set()
  const eventData = {}
  for (const name of eventNames) {
    eventData[name] = {}
    for (const s of data[name]) {
      allDates.add(s.test_date)
      eventData[name][s.test_date] = { numeric: s.numeric_value, raw: s.raw_value, score: s.earned_score, unit: s.unit, higher: s.higher_better }
    }
  }
  const dates = [...allDates].sort()
  const colors = ['#4f46e5', '#059669', '#d97706', '#dc2626', '#909399', '#7c3aed', '#36CFC9', '#FF85C0']

  const yAxes = []
  const series = eventNames.map((name, i) => {
    const side = i % 2 === 0 ? 'left' : 'right'
    const offset = Math.floor(i / 2) * 50
    const unit = data[name][0]?.unit || ''
    const higherBetter = data[name][0]?.higher_better
    yAxes.push({
      type: 'value', name: unit, nameTextStyle: { fontSize: 10 },
      position: side, offset: offset || undefined,
      axisLabel: { fontSize: 9 }, splitLine: { show: i === 0 },
      inverse: higherBetter === false
    })
    return {
      name, type: 'line', smooth: true, yAxisIndex: i,
      color: colors[i % colors.length],
      data: dates.map(d => {
        const pt = eventData[name][d]
        return pt ? { value: pt.numeric, raw: pt.raw, score: pt.score } : null
      }),
      label: { show: true, formatter: p => p.data ? `${p.data.raw} (${p.data.score}分)` : '', fontSize: 10 },
      symbol: 'circle', symbolSize: 6
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = params[0]?.axisValue || ''
        let tip = date + '<br/>'
        for (const p of params) {
          if (p.data) {
            const dir = data[p.seriesName]?.[0]?.higher_better ? '越大越好' : '越小越好'
            tip += `${p.marker} ${p.seriesName}: ${p.data.raw} (${p.data.score}分) ${dir}<br/>`
          }
        }
        return tip
      }
    },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 10 } },
    grid: { left: 45, right: 45, top: 10, bottom: 50 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: yAxes,
    series
  }
})
</script>

<style scoped>
/* ===== Dark Cockpit Variables ===== */
.stats-page {
  --bg-root: #0c1929; --bg-card: #132238; --bg-hover: #1a2f4a;
  --cyan: #06b6d4; --amber: #f59e0b; --emerald: #10b981; --red: #ef4444;
  --indigo: #818cf8; --gold: #f59e0b;
  --text-a: #f1f5f9; --text-b: #94a3b8; --text-c: #64748b;
  --border: #1e3a5f; --border-sub: #162942;
  background: var(--bg-root); margin: -12px; padding: 20px 24px 40px;
  min-height: calc(100vh - 50px); position: relative;
}
.stats-page::before {
  content: ''; position: absolute; inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0;
}
.stats-page > * { position: relative; z-index: 1; }

.back-btn { margin-bottom: 4px; color: var(--text-b); }
h3 { color: var(--text-a); }

/* ===== Element Plus overrides ===== */
.stats-page :deep(.el-tabs__header) { border-bottom-color: var(--border-sub); }
.stats-page :deep(.el-tabs__item) { color: var(--text-b); }
.stats-page :deep(.el-tabs__item.is-active) { color: var(--cyan); }
.stats-page :deep(.el-tabs__active-bar) { background: var(--cyan); }
.stats-page :deep(.el-input__wrapper) {
  background: #0f1e35;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: none;
}
.stats-page :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: var(--cyan);
  box-shadow: 0 0 0 1px rgba(6,182,212,0.15);
}
.stats-page :deep(.el-input__inner) { color: var(--text-a); }
.stats-page :deep(.el-button--default) { background: transparent; border-color: var(--border); color: var(--text-b); }
.stats-page :deep(.el-card) { background: var(--bg-card); border-color: var(--border-sub); color: var(--text-a); }
.stats-page :deep(.el-card__header) { padding: 10px 16px; font-size: 13px; font-weight: 600; color: var(--text-a); border-bottom-color: var(--border-sub); }
.stats-page :deep(.el-dialog) { background: var(--bg-card); border: 1px solid var(--border); }
.stats-page :deep(.el-dialog__title) { color: var(--text-a); }
.stats-page :deep(.el-pagination button), .stats-page :deep(.el-pager li) { color: var(--text-b); background: transparent; }
.stats-page :deep(.el-pager li.is-active) { background: var(--cyan); color: #fff; }

/* Context note */
.ctx-note {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; color: var(--text-c); margin-bottom: 16px;
}
.ctx-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--cyan); opacity: 0.5; }

/* Section label */
.section-label {
  font-size: 10.5px; font-weight: 700; color: var(--text-c);
  letter-spacing: 1px; text-transform: uppercase; margin-bottom: 10px;
  display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border-sub); }

/* ===== KPI Grid ===== */
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
@media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px) { .kpi-grid { grid-template-columns: 1fr; } }

.kpi-card {
  background: var(--bg-card); border: 1px solid var(--border-sub); border-radius: 14px;
  padding: 20px 22px; position: relative; overflow: hidden; transition: all 0.2s;
}
.kpi-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.3); transform: translateY(-1px); }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 14px; right: 14px; height: 3px; border-radius: 0 0 3px 3px; }
.kpi-card.indigo::before { background: var(--indigo); }
.kpi-card.gold::before { background: var(--gold); }
.kpi-card.amber::before { background: var(--amber); }

.kpi-label { font-size: 10.5px; font-weight: 600; letter-spacing: 0.8px; color: var(--text-c); text-transform: uppercase; margin-bottom: 6px; }
.kpi-value-row { display: flex; align-items: baseline; gap: 5px; }
.kpi-value { font-size: 34px; font-weight: 800; letter-spacing: -1px; line-height: 1; }
.kpi-card.indigo .kpi-value { color: var(--indigo); text-shadow: 0 0 20px rgba(129,140,248,0.2); }
.kpi-card.gold .kpi-value { color: var(--gold); text-shadow: 0 0 20px rgba(245,158,11,0.2); }
.kpi-card.amber .kpi-value { color: var(--amber); text-shadow: 0 0 20px rgba(245,158,11,0.2); }
.kpi-unit { font-size: 13px; font-weight: 500; color: var(--text-c); }
.kpi-sub { margin-top: 6px; font-size: 11px; color: var(--text-c); }

/* ===== Charts ===== */
.chart-card {
  background: var(--bg-card); border: 1px solid var(--border-sub); border-radius: 14px;
  padding: 16px 20px 10px;
}
.chart-title { font-size: 13px; font-weight: 600; color: var(--text-a); margin-bottom: 4px; }
.chart-subtitle { font-weight: 400; font-size: 10px; color: var(--text-c); margin-left: 6px; }

/* ===== Risk Grid ===== */
.risk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 768px) { .risk-grid { grid-template-columns: 1fr; } }

.risk-card { background: var(--bg-card); border: 1px solid var(--border-sub); border-radius: 14px; overflow: hidden; }
.risk-hd {
  padding: 14px 20px; border-bottom: 1px solid var(--border-sub);
  font-size: 13px; font-weight: 600; color: var(--text-a);
  display: flex; align-items: center; justify-content: space-between;
}
.risk-badge { padding: 2px 10px; border-radius: 12px; font-size: 10px; font-weight: 700; }
.risk-badge.red { background: rgba(239,68,68,0.15); color: var(--red); }
.risk-badge.amber-bg { background: rgba(245,158,11,0.15); color: var(--amber); }

.risk-list { padding: 4px 0; }
.risk-row { display: flex; align-items: center; gap: 10px; padding: 10px 20px; transition: background 0.15s; }
.risk-row:hover { background: var(--bg-hover); }
.risk-rank { width: 20px; text-align: center; font-size: 11px; font-weight: 700; color: var(--text-c); flex-shrink: 0; }
.risk-rank.top3 { color: var(--amber); }
.risk-info { flex: 1; min-width: 0; }
.risk-name { font-size: 12.5px; font-weight: 600; color: var(--text-a); }
.risk-meta { font-size: 10.5px; color: var(--text-c); margin-top: 1px; }
.risk-meta-inline { font-weight: 400; font-size: 10px; color: var(--text-c); }

.risk-bar-wrap { width: 70px; height: 5px; background: #162942; border-radius: 3px; overflow: hidden; flex-shrink: 0; }
.risk-bar-fill { height: 100%; border-radius: 3px; }
.risk-bar-fill.low { background: var(--red); }
.risk-bar-fill.mid { background: var(--amber); }

.risk-value { width: 42px; text-align: right; flex-shrink: 0; font-size: 12px; font-weight: 600; }
.risk-value.low { color: var(--red); }
.risk-value.mid { color: var(--amber); }

/* Student risk */
.student-risk-row { display: flex; align-items: center; gap: 10px; padding: 10px 20px; transition: background 0.15s; }
.student-risk-row:hover { background: var(--bg-hover); }
.student-avatar-sm {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; color: #fff;
}
.student-avatar-sm.male { background: #818cf8; }
.student-avatar-sm.female { background: #ec4899; }
.score-drop { color: var(--red); font-weight: 600; }

/* Grade block */
.grade-block { margin-bottom: 24px; }
.grade-label {
  font-size: 16px; font-weight: 700; color: var(--text-a);
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border-sub);
  display: flex; align-items: center; gap: 8px;
}
.grade-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); }

/* Student header */
.student-hd {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 22px; background: var(--bg-card); border-radius: 14px;
  border: 1px solid var(--border-sub); margin-bottom: 12px;
}
.student-avatar-lg {
  width: 44px; height: 44px; border-radius: 50%;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700;
}
.student-name-lg { font-size: 17px; font-weight: 700; color: var(--text-a); }
.student-meta-lg { font-size: 12px; color: var(--text-b); margin-top: 2px; }

/* Recommendation card */
.rec-card { background: var(--bg-card); border: 1px solid var(--border-sub); border-radius: 14px; padding: 18px 22px; margin-bottom: 12px; }
.rec-title { font-size: 13px; font-weight: 600; color: var(--text-a); margin-bottom: 10px; }
.rec-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; margin-bottom: 3px; font-size: 14px; color: var(--text-a); }
.rec-item.gold { background: rgba(245,158,11,0.12); }
.rec-item.silver { background: rgba(148,163,184,0.08); }
.rec-item.bronze { background: rgba(239,68,68,0.08); }
.rec-medal { font-size: 20px; }
.rec-event { font-weight: 600; }
.rec-score { margin-left: auto; font-weight: 700; color: var(--indigo); }

/* Empty state */
.empty-hint { text-align: center; color: var(--text-c); padding: 32px; font-size: 13px; }

/* Score table */
.score-table-wrap {
  background: var(--bg-card); border: 1px solid var(--border-sub); border-radius: 14px; overflow: hidden;
}
.score-table-wrap :deep(.el-table) { font-size: 12px; background: transparent; }
.score-table-wrap :deep(.el-table th) {
  background: #0f1e35; color: var(--text-b); font-weight: 600; font-size: 11px; padding: 10px 8px; border-bottom-color: var(--border);
}
.score-table-wrap :deep(.el-table td) { padding: 8px; border-bottom-color: var(--border-sub); background: transparent; color: var(--text-a); }
.score-table-wrap :deep(.el-table tr) { background: transparent; }
.score-table-wrap :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background: rgba(255,255,255,0.015); }
.score-table-wrap :deep(.el-table__body tr:hover td) { background: var(--bg-hover) !important; }
.cell-score { font-weight: 600; color: var(--text-a); }
.cell-best { color: var(--emerald); font-weight: 700; }
.cell-empty { color: #475569; }
.table-hint { padding: 8px 16px; font-size: 11px; color: var(--text-c); background: #0f1e35; }
</style>
