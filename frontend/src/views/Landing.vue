<template>
  <div class="landing" ref="root">
    <!-- ====================== NAVBAR ====================== -->
    <nav class="navbar">
      <div class="logo" @click="go('/')">🏃 体育中考智能管理平台</div>
      <div class="nav-anchors">
        <a href="#why">为什么用它</a>
        <a href="#features">核心能力</a>
        <a href="#proof">真实数据</a>
        <a href="#start">三步上线</a>
      </div>
      <button class="btn-cta" @click="go('/admin/login')">进入管理端体验</button>
    </nav>

    <!-- ====================== HERO ====================== -->
    <header class="hero">
      <div class="orb orb-a"></div>
      <div class="orb orb-b"></div>
      <div class="grid-lines"></div>
      <p class="eyebrow">面向学校 · 体育中考备考的数字化管理平台</p>
      <h1 class="hero-title">体育中考，一分都别丢<br /><span>满分率 · 差距 · 薄弱，全都看得见</span></h1>
      <p class="hero-sub">
        从日常测试录入到长跑人脸识别体测，一个平台把自动算分、满分率统计、
        班级与年级对比全部打通。<br class="hide-mobile" />
        校长与教务不翻 Excel，也知道全校该补谁、练什么。
      </p>
      <div class="hero-actions">
        <button class="btn-primary" @click="go('/admin/login')">进入管理端体验 →</button>
        <a class="btn-ghost" href="#features">看看它能做什么 ↓</a>
      </div>
      <div class="hero-chips">
        <span class="chip"><i class="dot"></i>云端托管 · 学校不用自建机房</span>
        <span class="chip"><i class="dot"></i>多校数据独立隔离</span>
        <span class="chip"><i class="dot"></i>浏览器即用 · 免安装</span>
        <span class="chip"><i class="dot"></i>体测设备离线也能跑</span>
      </div>
    </header>

    <!-- ====================== WHY / PAINS ====================== -->
    <section id="why" class="section">
      <div class="sec-head">
        <span class="kicker">学校体育备考的真实痛点</span>
        <h2 class="sec-title">数据没被用起来，才是最大的浪费</h2>
        <p class="sec-sub">每次测试都是一手真实数据——但它们躺在表格里时，谁也看不见差距在哪里。</p>
      </div>
      <div class="pain-grid">
        <div class="pain-card" v-for="p in pains" :key="p.title">
          <div class="pain-ico">{{ p.icon }}</div>
          <h3>{{ p.title }}</h3>
          <p>{{ p.desc }}</p>
        </div>
      </div>
      <div class="answer-banner">
        <p>这些，<span>一个平台</span>全收进统计里——自动算分、自动汇总、出错即暴露。</p>
      </div>
    </section>

    <!-- ====================== FEATURES ====================== -->
    <section id="features" class="section features">
      <div class="sec-head">
        <span class="kicker">核心能力</span>
        <h2 class="sec-title">从测试到统计，每一步都替老师做掉</h2>
        <p class="sec-sub">数据自动进系统、自动算分、自动汇总，老师把时间还给上课和补练。</p>
      </div>
      <div class="feat-grid">
        <div class="feat-card" v-for="f in feats" :key="f.title">
          <div class="feat-ico">{{ f.icon }}</div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- ====================== PROOF / REAL STATS ====================== -->
    <section id="proof" class="stats">
      <div class="wrap stats-inner">
        <div class="proof-head">
          <h2>不是演示 —— 是正在跑的线上数据</h2>
          <p>平台现网实时统计，每 24 小时自动备份，数据安全有兜底</p>
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

    <!-- ====================== HOW IT STARTS ====================== -->
    <section id="start" class="section">
      <div class="sec-head">
        <span class="kicker">三步上线</span>
        <h2 class="sec-title">不推翻现在的工作，从下一次测试就开始</h2>
        <p class="sec-sub">把现有班级、学生导进去，平台立刻就能跑起来。</p>
      </div>
      <div class="step-grid">
        <div class="step" v-for="(s, i) in steps" :key="s.title">
          <div class="step-no">{{ s.no }}</div>
          <h3>{{ s.title }}</h3>
          <p>{{ s.desc }}</p>
        </div>
      </div>
    </section>

    <!-- ====================== CTA ====================== -->
    <section class="cta">
      <h2>让这所学校的下一场体育测试，开始有数据</h2>
      <p>管理端、学生端、设备端都已就绪。</p>
      <div class="cta-btns">
        <button class="cta-btn" @click="go('/admin/login')">教师 · 管理端体验</button>
        <button class="cta-btn ghost" @click="go('/student/login')">学生 · 成绩查询</button>
        <button class="cta-btn ghost" @click="go('/run')">设备端 · 开始跑测</button>
      </div>
    </section>

    <!-- ====================== FOOTER ====================== -->
    <footer class="footer">
      <div class="footer-brand">🏃 体育中考智能管理平台</div>
      <div class="footer-links">
        <a @click="go('/admin/login')">管理端</a>
        <a @click="go('/student/login')">学生端</a>
        <a @click="go('/run')">设备端</a>
      </div>
      <p class="footer-copy">© 2026 体育中考智能管理平台 · 面向学校的体育成绩数字化管理</p>
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
  { label: '自动评分成绩', suffix: '条', value: stats.value?.scores ?? 0 },
  { label: '覆盖测试项目', suffix: '项', value: stats.value?.events ?? 0 },
])

const pains = [
  { icon: '📊', title: '成绩看不着全貌', desc: '分散在各班、各老师的表格里，想横向比较要靠手动汇总，月底才对得上账。' },
  { icon: '📐', title: '算分各写各的', desc: '每位老师一套换算口径，同一条成绩在不同班可能得到不同的分，无法横向比。' },
  { icon: '🎯', title: '补练全凭感觉', desc: '薄弱在哪个班、哪几个临界生，靠经验猜——练了半个月，看不到效果在哪。' },
  { icon: '⏱️', title: '长跑靠人工掐表', desc: '体测要专门安排老师计时登记，又累又容易记错，成绩还要二次录入。' },
]

const feats = [
  { icon: '🎯', title: '满分率 · 优秀率盯得住', desc: '按班级、年级实时对比满分率与优秀率，近 30 天最佳成绩趋势一目了然——备考进度、临界学生，打开就能看。' },
  { icon: '✍️', title: '录入即自动算分', desc: '手动录入、Excel 批量导入、体测设备上报三种入口，全校共用一套评分标准，算分口径从此统一。' },
  { icon: '📷', title: '人脸识别长跑体测', desc: '长跑测试用手机对准终点，人脸通过即自动计时、当场出成绩并入库——不用专门安排老师掐表。' },
  { icon: '📋', title: '考勤与成绩档案', desc: '出勤随手记，成绩长期归档、随时可查可导出。学期总结交给系统，不交 Excel。' },
]

const steps = [
  { no: '01', title: '配好项目与标准', desc: '建班级、批量导入学生，把考试项目与评分标准一次性配好，全校口径就统一了。' },
  { no: '02', title: '录入或直接跑测', desc: '平时测试手动/批量录入；长跑用人脸识别设备自动计时。成绩全部自动进系统。' },
  { no: '03', title: '盯统计、追补练', desc: '满分率、班级差距、临界学生自动汇总，教学调整有据可依，效果看得见。' },
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

.wrap { max-width: 1160px; margin: 0 auto; padding: 0 24px; }

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
  background: rgba(5, 11, 31, .84);
  border-bottom: 1px solid rgba(255, 255, 255, .08);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.logo { font-size: 18px; font-weight: 700; cursor: pointer; letter-spacing: .3px; }

.nav-anchors { display: flex; gap: 26px; }

.nav-anchors a { color: #aab4d6; text-decoration: none; font-size: 14px; transition: color .2s; }
.nav-anchors a:hover { color: #fff; }

.btn-cta {
  padding: 9px 18px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(90deg, #4f6cff, #6a5cff);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
  white-space: nowrap;
}

.btn-cta:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(79, 108, 255, .45); }

/* ====================== HERO ====================== */
.hero {
  position: relative;
  padding: 180px 24px 64px;
  text-align: center;
  overflow: hidden;
}

.orb { position: absolute; border-radius: 50%; filter: blur(90px); opacity: .5; pointer-events: none; }
.orb-a { width: 600px; height: 600px; top: -220px; left: 50%; transform: translateX(-75%); background: radial-gradient(circle, rgba(79, 108, 255, .55), transparent 65%); }
.orb-b { width: 460px; height: 460px; top: 30px; right: 50%; transform: translateX(35%); background: radial-gradient(circle, rgba(122, 92, 255, .4), transparent 65%); }

.grid-lines {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, .035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, .035) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%);
  -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%);
  pointer-events: none;
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
  margin-bottom: 26px;
}

.hero-title {
  position: relative;
  font-size: 58px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: .5px;
}

.hero-title span {
  background: linear-gradient(135deg, #4f6cff 0%, #a07bff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-sub {
  position: relative;
  margin: 24px auto 0;
  max-width: 700px;
  color: #a2adcf;
  font-size: 17px;
  line-height: 1.9;
}

.hero-actions {
  position: relative;
  margin-top: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.btn-primary {
  padding: 15px 32px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(90deg, #4f6cff, #6a5cff);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all .25s;
}

.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(79, 108, 255, .45); }

.btn-ghost {
  padding: 14px 26px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, .2);
  color: #cdd6f4;
  text-decoration: none;
  font-size: 15px;
  transition: all .25s;
}

.btn-ghost:hover { border-color: rgba(255, 255, 255, .4); background: rgba(255, 255, 255, .05); }

.hero-chips {
  position: relative;
  margin-top: 40px;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .09);
  color: #aab4d6;
  font-size: 13px;
}

.chip .dot { width: 6px; height: 6px; border-radius: 50%; background: #5b78ff; box-shadow: 0 0 8px #5b78ff; }

/* ====================== SECTION COMMON ====================== */
.section { max-width: 1160px; margin: 0 auto; padding: 96px 24px 40px; }

.sec-head { text-align: center; max-width: 760px; margin: 0 auto 46px; }

.kicker {
  display: inline-block;
  color: #8fa0ff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 3px;
  margin-bottom: 14px;
}

.sec-title {
  font-size: 38px;
  font-weight: 800;
  line-height: 1.4;
  margin-bottom: 14px;
  background: linear-gradient(135deg, #fff 0%, #a0b8ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.sec-sub { color: #93a0c6; font-size: 16px; line-height: 1.8; }

/* ====================== PAINS ====================== */
.pain-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}

.pain-card {
  padding: 26px 22px;
  background: rgba(255, 255, 255, .035);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 18px;
  transition: all .25s;
}

.pain-card:hover { border-color: rgba(255, 255, 255, .18); transform: translateY(-2px); }

.pain-ico { font-size: 30px; margin-bottom: 12px; opacity: .9; }

.pain-card h3 { font-size: 17px; font-weight: 700; margin-bottom: 8px; }

.pain-card p { color: #8d98bd; font-size: 14px; line-height: 1.75; }

.answer-banner {
  margin-top: 26px;
  padding: 22px 28px;
  text-align: center;
  border-radius: 16px;
  border: 1px solid rgba(79, 108, 255, .4);
  background: linear-gradient(120deg, rgba(79, 108, 255, .16), rgba(106, 92, 255, .1));
}

.answer-banner p { color: #dfe5ff; font-size: 18px; }
.answer-banner span {
  font-weight: 800;
  background: linear-gradient(90deg, #7f97ff, #b29bff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ====================== FEATURES ====================== */
.features { padding-top: 60px; }

.feat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
}

.feat-card {
  display: flex;
  gap: 18px;
  padding: 28px 26px;
  background: linear-gradient(165deg, rgba(255, 255, 255, .055), rgba(255, 255, 255, .02));
  border: 1px solid rgba(255, 255, 255, .09);
  border-radius: 20px;
  transition: all .25s;
}

.feat-card:hover {
  transform: translateY(-3px);
  border-color: rgba(79, 108, 255, .55);
  background: linear-gradient(165deg, rgba(79, 108, 255, .12), rgba(255, 255, 255, .02));
}

.feat-ico {
  flex: 0 0 52px;
  width: 52px; height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 27px;
  border-radius: 14px;
  background: rgba(79, 108, 255, .16);
  border: 1px solid rgba(79, 108, 255, .3);
}

.feat-card h3 { font-size: 19px; font-weight: 700; margin-bottom: 8px; }

.feat-card p { color: #9aa5c7; font-size: 14px; line-height: 1.8; }

/* ====================== PROOF / STATS ====================== */
.stats {
  margin-top: 80px;
  padding: 64px 0;
  background:
    radial-gradient(900px 260px at 50% 0%, rgba(79, 108, 255, .12), transparent),
    linear-gradient(180deg, transparent, rgba(79, 108, 255, .06), transparent);
  border-top: 1px solid rgba(255, 255, 255, .05);
  border-bottom: 1px solid rgba(255, 255, 255, .05);
}

.stats-inner { display: grid; grid-template-columns: 340px 1fr; gap: 48px; align-items: center; }

.proof-head h2 {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.45;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #fff 0%, #a0b8ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.proof-head p { color: #8d98bd; font-size: 14px; line-height: 1.8; }

.stat-list { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }

.stat {
  padding: 26px 16px;
  text-align: center;
  background: rgba(255, 255, 255, .045);
  border: 1px solid rgba(255, 255, 255, .09);
  border-radius: 18px;
  transition: all .25s;
}

.stat:hover { border-color: rgba(79, 108, 255, .55); transform: translateY(-2px); }

.stat-value {
  color: #7f97ff;
  font-size: 40px;
  font-weight: 800;
  line-height: 1.1;
}

.stat-unit { font-size: 16px; font-weight: 600; color: #a9b8ff; margin-left: 3px; }

.stat-label { margin-top: 10px; color: #9aa5c7; font-size: 13px; }

/* ====================== STEPS ====================== */
#start { padding-bottom: 90px; }

.step-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.step {
  position: relative;
  padding: 34px 26px 28px;
  background: rgba(255, 255, 255, .035);
  border: 1px solid rgba(255, 255, 255, .09);
  border-radius: 20px;
  transition: all .25s;
}

.step:hover { transform: translateY(-3px); border-color: rgba(79, 108, 255, .55); }

.step-no {
  position: absolute;
  top: 18px; right: 20px;
  font-size: 46px;
  font-weight: 800;
  line-height: 1;
  color: rgba(127, 151, 255, .25);
}

.step h3 { font-size: 19px; font-weight: 700; margin-bottom: 10px; }

.step p { color: #9aa5c7; font-size: 14px; line-height: 1.8; }

/* ====================== CTA ====================== */
.cta {
  margin: 10px 0 0;
  padding: 80px 24px;
  text-align: center;
  background:
    radial-gradient(800px 240px at 20% 0%, rgba(79, 108, 255, .28), transparent),
    linear-gradient(120deg, #14204d, #101736 55%, #1c1745);
  border-top: 1px solid rgba(255, 255, 255, .08);
}

.cta h2 { font-size: 34px; font-weight: 800; margin-bottom: 12px; }

.cta p { color: #a9b2d0; font-size: 16px; margin-bottom: 30px; }

.cta-btns { display: flex; justify-content: center; flex-wrap: wrap; gap: 16px; }

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

.cta-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 26px rgba(79, 108, 255, .45); }

.cta-btn.ghost { background: transparent; border: 1px solid rgba(255, 255, 255, .3); }
.cta-btn.ghost:hover { background: rgba(255, 255, 255, .08); }

/* ====================== FOOTER ====================== */
.footer { padding: 40px 24px 46px; text-align: center; border-top: 1px solid rgba(255, 255, 255, .05); }
.footer-brand { font-weight: 700; font-size: 15px; }
.footer-links { display: flex; justify-content: center; gap: 22px; margin-top: 14px; }
.footer-links a { color: #9aa5c7; font-size: 13px; cursor: pointer; }
.footer-links a:hover { color: #fff; }
.footer-copy { margin-top: 18px; color: #6b749a; font-size: 12px; }

/* ====================== RESPONSIVE ====================== */
@media (max-width: 1024px) {
  .pain-grid { grid-template-columns: repeat(2, 1fr); }
  .stats-inner { grid-template-columns: 1fr; text-align: center; }
  .hero-title { font-size: 46px; }
  .sec-title { font-size: 32px; }
  .nav-anchors { display: none; }
}

@media (max-width: 767px) {
  .navbar { padding: 0 16px; }
  .logo { font-size: 14px; }
  .btn-cta { padding: 8px 13px; font-size: 13px; }
  .hero { padding: 140px 20px 48px; }
  .hero-title { font-size: 33px; }
  .hero-sub { font-size: 15px; }
  .hide-mobile { display: none; }
  .hero-chips { gap: 8px; }
  .chip { font-size: 12px; padding: 6px 11px; }
  .sec-title { font-size: 27px; }
  .section { padding: 64px 20px 24px; }
  .pain-grid { grid-template-columns: 1fr; }
  .answer-banner p { font-size: 16px; }
  .feat-grid { grid-template-columns: 1fr; }
  .feat-card { padding: 22px 18px; }
  .stat-list { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .stat-value { font-size: 32px; }
  .step-grid { grid-template-columns: 1fr; }
  .cta h2 { font-size: 26px; }
  .cta-btns { flex-direction: column; align-items: center; }
  .cta-btn { width: min(320px, 100%); }
}
</style>
