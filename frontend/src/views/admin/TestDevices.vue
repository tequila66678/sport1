<template>
  <div class="hub">
    <div class="hub-head">
      <h1>🏃 项目测试</h1>
      <p>选择要进行的测试项目。不同项目可能需要对应硬件，按卡片提示准备即可。</p>
    </div>

    <div class="dev-grid">
      <div v-for="d in devices" :key="d.key" class="dev-card">
        <div class="dev-emoji">{{ d.emoji }}</div>
        <div class="dev-name">{{ d.name }}</div>
        <div v-if="d.unit" class="dev-unit">{{ d.unit }}</div>
        <div class="dev-desc">{{ d.desc }}</div>
        <div class="dev-hw">🔧 {{ d.hw }}</div>
        <button class="open-btn" @click="openDevice(d)">进入测试 →</button>
      </div>
    </div>

    <p v-if="!devices.length" class="empty">暂无可用测试。联系管理员配置。</p>
  </div>
</template>

<script setup>
// 未来的其他测试（引体向上、立定跳远…）只需往 devices 里加一条：
// { key:'pullup', emoji:'🤸', name:'引体向上', unit:'', desc:'…', hw:'…', url:'/run-pullup' }
const devices = [
  {
    key: 'longrun',
    emoji: '🏃',
    name: '长跑测试',
    unit: '800米 / 1000米',
    desc: '终点设备：学生跑完站到镜头前，人脸识别自动记录成绩；男生自动记 1000 米、女生 800 米，识别不到可输学号兜底。',
    hw: '手机或平板（需摄像头），浏览器打开后用网页即可',
    url: '/run',
  },
]

function openDevice(d) {
  // 设备页是全屏独立页面，新标签页打开，后台这边不会跳走
  window.open(d.url, '_blank')
}
</script>

<style scoped>
.hub {
  margin: -12px; padding: 20px 24px 40px;
  min-height: calc(100vh - 50px);
  background: radial-gradient(circle at top, #112b72, #07142f 50%, #020817 100%);
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  max-width: 1100px; margin-left: auto; margin-right: auto;
}
.hub-head h1 { color: #fff; font-size: 28px; margin: 0 0 6px; }
.hub-head p { color: #8fa3d8; font-size: 14px; margin: 0 0 22px; }

.dev-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.dev-card {
  background: rgba(12,26,61,0.65); backdrop-filter: blur(16px);
  border: 1px solid rgba(90,120,255,0.15); border-radius: 20px;
  padding: 20px; display: flex; flex-direction: column;
  box-shadow: 0 0 30px rgba(80,120,255,0.06);
}
.dev-emoji { font-size: 40px; line-height: 1; }
.dev-name { color: #fff; font-size: 19px; font-weight: 700; margin: 12px 0 2px; }
.dev-unit { color: #a0b8ff; font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.dev-desc { color: #c0d0f0; font-size: 13.5px; line-height: 1.7; flex: 1; }
.dev-hw {
  color: #fcd34d; font-size: 12.5px; background: rgba(252,211,77,0.08);
  border: 1px solid rgba(252,211,77,0.15); border-radius: 10px;
  padding: 7px 10px; margin: 12px 0; line-height: 1.5;
}
.open-btn {
  border: none; cursor: pointer; border-radius: 12px; padding: 11px 0;
  background: linear-gradient(90deg, #2563eb, #3b82f6); color: #fff;
  font-size: 15px; font-weight: 600; font-family: inherit;
}
.open-btn:hover { filter: brightness(1.1); }
.empty { color: #7d8fb9; padding: 30px 0; text-align: center; }

@media (max-width: 767px) {
  .hub { padding: 12px; }
  .hub-head h1 { font-size: 22px; }
}
</style>
