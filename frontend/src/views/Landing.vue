<template>
  <div class="landing" ref="root">
    <!-- ====================== NAVBAR ====================== -->
    <nav class="navbar">
      <div class="logo" @click="go('/')">🏃 体育成绩智能管理平台</div>
      <div class="nav-right">
        <a class="nav-anchor" href="#stats">运行数据</a>
        <a class="nav-anchor" href="#features">功能</a>
        <button class="btn-login" @click="go('/admin/login')">管理端登录</button>
      </div>
    </nav>

    <!-- ====================== HERO ====================== -->
    <header class="hero">
      <div class="orb orb-a"></div>
      <div class="orb orb-b"></div>
      <p class="eyebrow">面向学校体育课与体测的成绩管理平台</p>
      <h1 class="hero-title">数据驱动教学<br /><span>让每个学生都更好</span></h1>
      <p class="hero-sub">长跑自动计时评分 · 学生成绩档案 · 班级年级多维统计与考勤<br class="hide-mobile" />一部手机加一台电脑，替掉你的 Excel。</p>
    </header>

    <!-- ====================== ENTRIES ====================== -->
    <section class="entries wrap">
      <h2 class="sec-title">进入系统</h2>
      <div class="entry-card" @click="go('/admin/login')">
        <div class="entry-ico">🛠️</div>
        <div class="entry-txt">
          <div class="entry-title">教师 · 管理端</div>
          <div class="entry-desc">录入与批量导入成绩 · 管理班级学生 · 配置测试项目与评分标准</div>
        </div>
        <div class="entry-go">进入 →</div>
      </div>
      <div class="entry-card" @click="go('/student/login')">
        <div class="entry-ico">📖</div>
        <div class="entry-txt">
          <div class="entry-title">学生 · 成绩查询</div>
          <div class="entry-desc">输入学号，查看自己的成绩与得分</div>
        </div>
        <div class="entry-go">进入 →</div>
      </div>
      <div class="entry-card" @click="go('/run')">
        <div class="entry-ico">📱</div>
        <div class="entry-txt">
          <div class="entry-title">体测设备端</div>
          <div class="entry-desc">手机人脸识别自动计时 · 离线也能跑测</div>
        </div>
        <div class="entry-go">打开 →</div>
      </div>
    </section>

    <!-- ====================== REAL STATS ====================== -->
    <section id="stats" class="stats">
      <div class="wrap stats-inner">
        <div class="stats-head">
          <h2 class="sec-title">正在运行</h2>
          <p>平台当前的实际管理规模（实时数据）</p>
        </div>
        <div class="stat-list">
          <div class="stat" v-for="k in kpis" :key="k.label">
            <div class="stat-value">
              <span class="stat-num" :data-target="k.value">0</span><span class="stat-unit">{{ k.suffix }}</span>
            </div>
            <div class="stat-label">{{ k.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====================== FEATURES ====================== -->
    <section id="features" class="features wrap">
      <h2 class="sec-title">它帮你做什么</h2>
      <div class="feat-grid">
        <div class="feat-card" v-for="f in feats" :key="f.title">
          <div class="feat-ico">{{ f.icon }}</div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- ====================== CTA ====================== -->
    <section class="cta">
      <h2>现在就能开始</h2>
      <p>成绩跑出来，统计自然有。</p>
      <div class="cta-btns">
        <button class="cta-btn" @click="go('/admin/login')">教师 · 管理成绩</button>
        <button class="cta-btn ghost" @click="go('/student/login')">学生 · 查询成绩</button>
        <button class="cta-btn ghost" @click="go('/run')">设备 · 开始跑测</button>
      </div>
    </section>

    <!-- ====================== FOOTER ====================== -->
    <footer class="footer">
      <div class="footer-brand">🏃 体育成绩智能管理平台</div>
      <div class="footer-links">
        <a @click="go('/admin/login')">管理端</a>
        <a @click="go('/student/login')">学生端</a>
        <a @click="go('/run')">设备端</a>
      </div>
      <p class="footer-copy">© 2026 体育成绩智能管理平台</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const root = ref(null)
const stats = ref(null)

const kpis = computed(() => [
  { label: '服务学校', suffix: '所', value: stats.value?.schools ?? 0 },
  { label: '在管学生', suffix: '名', value: stats.value?.students ?? 0 },
  { label: '覆盖测试项目', suffix: '项', value: stats.value?.events ?? 0 },
  { label: '成绩记录', suffix: '条', value: stats.value?.scores ?? 0 },
])

const feats = [
  { icon: '⏱️', title: '长跑自动评分', desc: '800 米 / 1000 米输入或设备上报后，按对应标准自动换算成绩与得分，男女分线、不靠人记。' },
  { icon: '📊', title: '驾驶舱统计', desc: '满分率、优秀率、合格率，班级与年级对比、近 30 天最佳成绩趋势，一屏掌握教学成效。' },
  { icon: '📷', title: '人脸识别体测', desc: '手机对准终点自动记时，离线也能跑测，一台手机就是一个体测点，成绩实时同步。' },
  { icon: '📋', title: '考勤与档案', desc: '出勤记录、学生成绩档案与列表导出，替代纸质与 Excel，班级数据随换随取。' },
]

function go(path) {
  router.push(path)
}

function animateCount(el, target, duration = 1400) {
  if (!el) return
  const start = 0
  const startTime = performance.now()
  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    el.textContent = Math.round(start + (target - start) * eased).toLocaleString('zh-CN')
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

onMounted(async () => {
  try {
    const res = await api.get('/config/public/stats')
    if (res.data) stats.value = res.data
  } catch { /* 统计接口不可用时保持 0，不阻断首页 */ }
  await nextTick()
  root.value?.querySelectorAll('.stat-num').forEach((el, i) => {
    setTimeout(() => animateCount(el, Number(el.dataset.target || 0)), i * 120)
  })
})
</script>

<style scoped>
/* ====================== BASE ====================== */
.landing {
  min-height: 100vh;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #050b1f;
  color: #fff;
  overflow-x: hidden;
}

.wrap {
  max-width: 1160px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ====================== NAVBAR ====================== */
.navbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background: rgba(5, 11, 31, .82);
  border-bottom: 1px solid rgba(255, 255, 255, .08);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.logo {
  font-size: 19px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: .5px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 26px;
}

.nav-anchor {
  color: #aab4d6;
  text-decoration: none;
  font-size: 14px;
  transition: color .2s;
}

.nav-anchor:hover { color: #fff; }

.btn-login {
  padding: 8px 18px;
  border-radius: 10px;
  border: 1px solid #315eff;
  background: rgba(49, 94, 255, .12);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all .2s;
}

.btn-login:hover {
  background: rgba(49, 94, 255, .25);
}

/* ====================== HERO ====================== */
.hero {
  position: relative;
  padding: 168px 24px 0;
  text-align: center;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: .55;
  pointer-events: none;
}

.orb-a {
  width: 520px; height: 520px;
  top: -180px; left: 50%;
  transform: translateX(-70%);
  background: radial-gradient(circle, rgba(79, 108, 255, .5), transparent 65%);
}

.orb-b {
  width: 420px; height: 420px;
  top: 40px; right: 50%;
  transform: translateX(30%);
  background: radial-gradient(circle, rgba(106, 92, 255, .35), transparent 65%);
}

.eyebrow {
  position: relative;
  display: inline-block;
  padding: 7px 18px;
  border: 1px solid rgba(255, 255, 255, .12);
  border-radius: 999px;
  background: rgba(255, 255, 255, .05);
  color: #9fb0ff;
  font-size: 14px;
  letter-spacing: 1px;
  margin-bottom: 28px;
}

.hero-title {
  position: relative;
  font-size: 66px;
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #fff 0%, #b9c9ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-title span {
  background: linear-gradient(135deg, #4f6cff 0%, #8a7bff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-sub {
  position: relative;
  margin: 26px auto 0;
  max-width: 640px;
  color: #9aa5c7;
  font-size: 18px;
  line-height: 1.9;
}

/* ====================== ENTRIES ====================== */
.entries {
  position: relative;
  padding-top: 64px;
  display: grid;
  gap: 14px;
}

.sec-title {
  text-align: center;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: .5px;
  margin-bottom: 30px;
  background: linear-gradient(135deg, #fff 0%, #a0b8ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.entry-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: linear-gradient(160deg, rgba(255, 255, 255, .06), rgba(255, 255, 255, .025));
  border: 1px solid rgba(255, 255, 255, .1);
  border-radius: 18px;
  cursor: pointer;
  transition: all .25s;
}

.entry-card:hover {
  background: linear-gradient(160deg, rgba(79, 108, 255, .18), rgba(255, 255, 255, .04));
  border-color: rgba(79, 108, 255, .55);
  transform: translateY(-2px);
}

.entry-ico {
  width: 52px; height: 52px;
  flex: 0 0 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  border-radius: 14px;
  background: rgba(79, 108, 255, .16);
  border: 1px solid rgba(79, 108, 255, .3);
}

.entry-txt { flex: 1; }

.entry-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
}

.entry-desc {
  color: #9aa5c7;
  font-size: 14px;
  line-height: 1.6;
}

.entry-go {
  color: #7f97ff;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}

/* ====================== STATS ====================== */
.stats {
  margin-top: 72px;
  padding: 60px 0;
  background: linear-gradient(180deg, transparent, rgba(79, 108, 255, .08), transparent);
  border-top: 1px solid rgba(255, 255, 255, .05);
  border-bottom: 1px solid rgba(255, 255, 255, .05);
}

.stats-inner {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 48px;
  align-items: center;
}

.stats-head .sec-title { text-align: left; margin-bottom: 8px; }

.stats-head p { color: #8d97bb; font-size: 15px; }

.stat-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}

.stat {
  padding: 26px 18px;
  text-align: center;
  background: rgba(255, 255, 255, .045);
  border: 1px solid rgba(255, 255, 255, .09);
  border-radius: 18px;
  transition: all .25s;
}

.stat:hover {
  background: rgba(255, 255, 255, .07);
  border-color: rgba(79, 108, 255, .5);
  transform: translateY(-2px);
}

.stat-value {
  color: #7f97ff;
  font-size: 40px;
  font-weight: 800;
  line-height: 1.1;
}

.stat-unit {
  font-size: 17px;
  font-weight: 600;
  color: #a9b8ff;
  margin-left: 3px;
}

.stat-label {
  margin-top: 10px;
  color: #9aa5c7;
  font-size: 13px;
}

/* ====================== FEATURES ====================== */
.features {
  padding: 84px 24px 60px;
}

.feat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.feat-card {
  padding: 30px 24px;
  background: linear-gradient(165deg, rgba(255, 255, 255, .055), rgba(255, 255, 255, .02));
  border: 1px solid rgba(255, 255, 255, .09);
  border-radius: 20px;
  transition: all .25s;
}

.feat-card:hover {
  transform: translateY(-4px);
  border-color: rgba(79, 108, 255, .5);
  background: linear-gradient(165deg, rgba(79, 108, 255, .12), rgba(255, 255, 255, .02));
}

.feat-ico { font-size: 34px; margin-bottom: 14px; }

.feat-card h3 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.feat-card p {
  color: #9aa5c7;
  font-size: 14px;
  line-height: 1.75;
}

/* ====================== CTA ====================== */
.cta {
  margin: 20px 0 0;
  padding: 76px 24px;
  text-align: center;
  background:
    radial-gradient(800px 220px at 20% 0%, rgba(79, 108, 255, .28), transparent),
    linear-gradient(120deg, #14204d, #101736 55%, #1c1745);
  border-top: 1px solid rgba(255, 255, 255, .08);
}

.cta h2 {
  font-size: 38px;
  font-weight: 800;
  margin-bottom: 10px;
}

.cta p {
  color: #a9b2d0;
  font-size: 17px;
  margin-bottom: 30px;
}

.cta-btns {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 16px;
}

.cta-btn {
  padding: 13px 30px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(90deg, #4f6cff, #6a5cff);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
}

.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 26px rgba(79, 108, 255, .45);
}

.cta-btn.ghost {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, .3);
}

.cta-btn.ghost:hover { background: rgba(255, 255, 255, .08); }

/* ====================== FOOTER ====================== */
.footer {
  padding: 40px 24px 48px;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, .05);
}

.footer-brand { font-weight: 700; font-size: 15px; }

.footer-links {
  display: flex;
  justify-content: center;
  gap: 22px;
  margin-top: 14px;
}

.footer-links a {
  color: #9aa5c7;
  font-size: 13px;
  cursor: pointer;
}

.footer-links a:hover { color: #fff; }

.footer-copy {
  margin-top: 18px;
  color: #6b749a;
  font-size: 12px;
}

/* ====================== RESPONSIVE ====================== */
@media (max-width: 1024px) {
  .stats-inner { grid-template-columns: 1fr; text-align: center; }
  .stats-head .sec-title { text-align: center; }
  .feat-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-title { font-size: 52px; }
}

@media (max-width: 767px) {
  .navbar { padding: 0 16px; }
  .logo { font-size: 15px; }
  .nav-anchor { display: none; }
  .btn-login { padding: 7px 14px; font-size: 13px; }
  .hero { padding-top: 132px; }
  .hero-title { font-size: 38px; }
  .hero-sub { font-size: 16px; }
  .hide-mobile { display: none; }
  .sec-title { font-size: 27px; }
  .entry-desc { display: none; }
  .entry-title { font-size: 16px; }
  .stat-list { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .stat-value { font-size: 32px; }
  .feat-grid { grid-template-columns: 1fr; }
  .cta h2 { font-size: 28px; }
  .cta-btns { flex-direction: column; align-items: center; }
  .cta-btn { width: min(320px, 100%); }
}
</style>
