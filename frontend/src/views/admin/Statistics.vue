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
/* ===== Variables ===== */
:root {
  --bg-root: #f6f5f3;
  --border: #e8e6e1;
  --indigo: #4f46e5;
  --gold: #b8860b;
  --amber: #d97706;
  --red: #dc2626;
  --text-a: #171717;
  --text-b: #525252;
  --text-c: #a3a3a3;
}

.back-btn { margin-bottom: 4px; }

/* Context note */
.ctx-note {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; color: #a3a3a3;
  margin-bottom: 16px;
}
.ctx-dot { width: 4px; height: 4px; border-radius: 50%; background: #4f46e5; opacity: 0.35; }

/* Section label */
.section-label {
  font-size: 12px; font-weight: 700; color: #525252;
  letter-spacing: 0.5px; text-transform: uppercase;
  margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: #e8e6e1; }

/* ===== KPI Grid ===== */
.kpi-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 12px; margin-bottom: 16px;
}
@media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px) { .kpi-grid { grid-template-columns: 1fr; } }

.kpi-card {
  background: #fff; border: 1px solid #e8e6e1; border-radius: 16px;
  padding: 20px 22px; position: relative; overflow: hidden;
  transition: all 0.2s;
}
.kpi-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-1px); }
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 14px; right: 14px;
  height: 3px; border-radius: 0 0 3px 3px;
}
.kpi-card.indigo::before { background: #4f46e5; }
.kpi-card.gold::before { background: #b8860b; }
.kpi-card.amber::before { background: #d97706; }

.kpi-label {
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.8px;
  color: #a3a3a3; text-transform: uppercase; margin-bottom: 6px;
}
.kpi-value-row { display: flex; align-items: baseline; gap: 5px; }
.kpi-value { font-size: 34px; font-weight: 800; letter-spacing: -1px; line-height: 1; }
.kpi-card.indigo .kpi-value { color: #4f46e5; }
.kpi-card.gold .kpi-value { color: #b8860b; }
.kpi-card.amber .kpi-value { color: #d97706; }
.kpi-unit { font-size: 13px; font-weight: 500; color: #a3a3a3; }
.kpi-sub { margin-top: 6px; font-size: 11px; color: #a3a3a3; }

/* ===== Trend Grid ===== */
.trend-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px; margin-bottom: 16px;
}
@media (max-width: 768px) { .trend-grid { grid-template-columns: 1fr; } }

.chart-card {
  background: #fff; border: 1px solid #e8e6e1; border-radius: 16px;
  padding: 16px 20px 10px;
}
.chart-title { font-size: 13px; font-weight: 600; color: #171717; margin-bottom: 4px; }
.chart-subtitle { font-weight: 400; font-size: 10px; color: #a3a3a3; margin-left: 6px; }

/* ===== Risk Grid ===== */
.risk-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (max-width: 768px) { .risk-grid { grid-template-columns: 1fr; } }

.risk-card {
  background: #fff; border: 1px solid #e8e6e1; border-radius: 16px; overflow: hidden;
}
.risk-hd {
  padding: 14px 20px; border-bottom: 1px solid #e8e6e1;
  font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: space-between;
}
.risk-badge { padding: 2px 10px; border-radius: 12px; font-size: 10px; font-weight: 700; }
.risk-badge.red { background: #fef2f2; color: #dc2626; }
.risk-badge.amber-bg { background: #fffbeb; color: #92400e; }

.risk-list { padding: 4px 0; }
.risk-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; transition: background 0.15s;
}
.risk-row:hover { background: #fafaf9; }
.risk-rank { width: 20px; text-align: center; font-size: 11px; font-weight: 700; color: #a3a3a3; flex-shrink: 0; }
.risk-rank.top3 { color: #d97706; }
.risk-info { flex: 1; min-width: 0; }
.risk-name { font-size: 12.5px; font-weight: 600; color: #171717; }
.risk-meta { font-size: 10.5px; color: #a3a3a3; margin-top: 1px; }
.risk-meta-inline { font-weight: 400; font-size: 10px; color: #a3a3a3; }

.risk-bar-wrap { width: 70px; height: 5px; background: #f5f3f0; border-radius: 3px; overflow: hidden; flex-shrink: 0; }
.risk-bar-fill { height: 100%; border-radius: 3px; }
.risk-bar-fill.low { background: #dc2626; }
.risk-bar-fill.mid { background: #d97706; }

.risk-value { width: 42px; text-align: right; flex-shrink: 0; font-size: 12px; font-weight: 600; }
.risk-value.low { color: #dc2626; }
.risk-value.mid { color: #d97706; }

/* Student risk */
.student-risk-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  padding: 8px 0;
}
.student-risk-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; transition: background 0.15s;
}
.student-risk-row:hover { background: #fafaf9; }
.student-avatar-sm {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; color: #fff;
}
.student-avatar-sm.male { background: #6366f1; }
.student-avatar-sm.female { background: #ec4899; }
.score-drop { color: #dc2626; font-weight: 600; }

/* Grade block */
.grade-block { margin-bottom: 24px; }
.grade-label {
  font-size: 16px; font-weight: 700; color: #171717;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid #e8e6e1;
  display: flex; align-items: center; gap: 8px;
}
.grade-dot { width: 7px; height: 7px; border-radius: 50%; background: #4f46e5; }

/* Student header */
.student-hd {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 22px; background: #fefdfb; border-radius: 14px;
  border: 1px solid #e8e6e1; margin-bottom: 12px;
}
.student-avatar-lg {
  width: 44px; height: 44px; border-radius: 50%;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700;
}
.student-name-lg { font-size: 17px; font-weight: 700; }
.student-meta-lg { font-size: 12px; color: #525252; margin-top: 2px; }

/* Recommendation card */
.rec-card { background: #fff; border: 1px solid #e8e6e1; border-radius: 14px; padding: 18px 22px; margin-bottom: 12px; }
.rec-title { font-size: 13px; font-weight: 600; margin-bottom: 10px; }
.rec-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; margin-bottom: 3px; font-size: 14px; }
.rec-item.gold { background: #fffbeb; }
.rec-item.silver { background: #f8fafc; }
.rec-item.bronze { background: #fef2f2; }
.rec-medal { font-size: 20px; }
.rec-event { font-weight: 600; }
.rec-score { margin-left: auto; font-weight: 700; color: #4f46e5; }

/* Empty state */
.empty-hint { text-align: center; color: #a3a3a3; padding: 32px; font-size: 13px; }

/* Score table */
.score-table-wrap { background: #fff; border: 1px solid #e8e6e1; border-radius: 14px; overflow: hidden; }
.score-table-wrap :deep(.el-table) { font-size: 12px; }
.score-table-wrap :deep(.el-table th) { background: #fafaf9; color: #525252; font-weight: 600; font-size: 11px; padding: 10px 8px; }
.score-table-wrap :deep(.el-table td) { padding: 8px; }
.cell-score { font-weight: 600; color: #171717; }
.cell-best { color: #059669; font-weight: 700; }
.cell-empty { color: #d4d4d4; }
.table-hint { padding: 8px 16px; font-size: 11px; color: #a3a3a3; background: #fafaf9; }

/* Override element-plus card headers to be cleaner */
:deep(.el-card__header) { padding: 10px 16px; font-size: 13px; font-weight: 600; }
</style>
