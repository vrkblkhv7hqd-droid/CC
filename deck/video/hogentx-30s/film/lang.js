// ---------- copy + type settings per language (?lang=zh | en) ----------
const LANG = new URLSearchParams(location.search).get('lang') || 'zh';
const EN = LANG === 'en';
// headline style: CJK reveals character by character; Latin reveals word by word, tighter tracking
const HL = EN
  ? { w: 800, size: 104, ls: -3, st: 0.075, by: 'word', lead: 118 }
  : { w: 900, size: 104, ls: 0, st: 0.042, by: 'char', lead: 130 };
const BODY = EN ? { ls: 0.2, st: 0.045, by: 'word' } : { ls: 1, st: 0.02, by: 'char' };
const S = EN ? {
  night: {
    kicker: 'EVERY HOTEL, EVERY DAY', kls: 5, ksize: 23,
    h: ['Hotel revenue leaks.', 'A little, every day.'],
    sub: 'Rarely in one big loss. It slips away quietly, room by room.',
    leaks: ['Empty rooms spotted late', 'Rates set too low', 'Rooms left unsold', 'Reviews left unanswered'],
    leakSize: 26,
  },
  intro: {
    h: ['AI employees', 'that know how', 'to run a hotel.'],
    tags: ['Rates', 'Room status', 'Reviews', 'Quality'], tagSize: 34,
    sub: 'Brief them in one sentence. They get to work.',
  },
  roles: [
    { k: 'DIGITAL EMPLOYEE', title: 'Revenue Manager', tasks: ['Competitor rates', 'Booking pace', 'Multi-channel repricing'] },
    { k: 'DIGITAL EMPLOYEE', title: 'Guest Relations', tasks: ['Tracks guest feedback', 'Drafts replies', 'Posts on approval'] },
    { k: 'DIGITAL EMPLOYEE', title: 'Quality Inspector', tasks: ['Inspection plans', 'Fix follow-ups', 'Sign-off & reporting'] },
    { k: 'DIGITAL EMPLOYEE', title: 'GM’s Assistant', tasks: ['Daily morning brief', 'Priorities & anomaly alerts'] },
  ],
  roleTitle: { w: 800, size: 106, ls: -3.2, st: 0.09, by: 'word' },
  ui: {
    pillA: 'Rate suggestion · pending', pillB: 'Approved by manager · applied', pillSize: 25,
    draft: 'AI reply draft', post: 'Approve & post', posted: 'Posted',
    qTitle: 'Inspection tasks', qRows: ['Room cleanliness', 'Facilities', 'Fix verification'], qTodo: 'Pending', qDone: 'Passed', qFinal: 'Signed off',
    bTitle: 'Morning brief', bTime: '8:00 AM', bRows: ['Rate suggestions', 'Review replies', 'Quality fixes', 'Price anomalies'],
    rowSize: 27, uiLs: 0,
  },
  proof: {
    kicker: 'FIELD TEST', kicker2: '29 HOTELS · 6 ROUTINE TASKS · WEEKLY TIME', kx: -616,
    unit: 'min', per: '/ week', label: 'Weekly time on 6 routine tasks',
    before: 'Before', after: 'After', less: 'TIME SPENT',
    note: 'Scope: 29 hotels run under our own brand (China) · Metric: total weekly time on 6 tasks for one manager running 2 hotels · Source: internal operations feedback',
    noteSize: 19,
  },
  end: { tag: 'Every room, sold at the price it deserves.', tagSize: 64, tagLs: -1, tagSt: 0.075, desc: 'AI digital employees for hotels', url: 'hogentx.com' },
} : {
  night: {
    kicker: '酒店的日常', kls: 8, ksize: 28,
    h: ['酒店的收入，', '每天都在漏掉一点。'],
    sub: 'Hotel revenue rarely vanishes at once. It leaks — a little, every day.',
    leaks: ['空房发现太晚', '价格偏低少收', '有房漏卖', '差评没回'],
    leakSize: 29,
  },
  intro: {
    h: ['懂经营的', '酒店 AI 数字员工'],
    tags: ['盯价格', '盯房态', '回点评', '管质检'], tagSize: 37,
    sub: 'AI digital employees that know how to run a hotel.',
  },
  roles: [
    { k: 'REVENUE MANAGER', title: '数字收益经理', tasks: ['竞品价格对比', '预订进度监测', '多平台改价'] },
    { k: 'GUEST RELATIONS', title: '数字宾客关系专员', tasks: ['关注宾客反馈', '起草差评回复', '确认后发布'] },
    { k: 'QUALITY INSPECTOR', title: '数字质检主管', tasks: ['质检计划与任务', '整改跟进', '验收与统计'] },
    { k: 'GM’S ASSISTANT', title: '数字总经理助理', tasks: ['每日早安简报', '重点事项与异常提醒'] },
  ],
  roleTitle: { w: 900, size: 116, ls: 0, st: 0.042, by: 'char' },
  ui: {
    pillA: '调价建议 · 待确认', pillB: '经理已确认 · 执行', pillSize: 27,
    draft: 'AI 回复草稿', post: '确认发布', posted: '已发布',
    qTitle: '质检任务', qRows: ['客房卫生', '设施设备', '整改复核'], qTodo: '待检', qDone: '已通过', qFinal: '验收通过',
    bTitle: '早安简报', bTime: '08:00', bRows: ['调价建议', '差评回复', '质检整改', '订单价格异常'],
    rowSize: 29, uiLs: 1,
  },
  proof: {
    kicker: '住小叮实验', kicker2: '29 HOTELS · 6 ROUTINE TASKS · WEEKLY TIME', kx: -548,
    unit: '分钟', per: '/ 周', label: '6 项日常任务，每周合计用时',
    before: '使用前', after: '使用后', less: '用时减少',
    note: '实验范围：自有品牌「住小叮」29 家酒店（中国）· 口径：一位经理管理 2 家酒店时，6 项任务每周合计用时 · 来源：内部业务反馈',
    noteSize: 20,
  },
  end: { tag: '让每一间房，卖出它该有的价钱。', tagSize: 64, tagLs: 8, tagSt: 0.036, desc: '懂经营的酒店 AI 数字员工', url: 'hogentx.com' },
};
