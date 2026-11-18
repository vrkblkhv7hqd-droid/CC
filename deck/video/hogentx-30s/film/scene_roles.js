// ---------- ACT II: daylight. four digital employees, four stops on the line ----------
function drawPaperBg(t, cam) {
  g.fillStyle = C.paper; g.fill();
  const rg = g.createRadialGradient(520, 260, 0, 520, 260, 1300);
  rg.addColorStop(0, 'rgba(255,255,255,.9)'); rg.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = rg; g.fill();
}
// faint lattice in the two logo directions (world attached -> streaks into speed lines)
function lattice(cam, colA, colB, lw = 1.5) {
  const sp = 190, R = 1500 / cam.z;
  // parallel to the link
  const pc = (cam.x - L0[0]) * -U[1] + (cam.y - L0[1]) * U[0];      // perpendicular coordinate of the camera
  const sc = (cam.x - L0[0]) * U[0] + (cam.y - L0[1]) * U[1];
  g.lineWidth = lw; g.lineCap = 'butt';
  g.strokeStyle = colA; g.beginPath();
  for (let k = Math.floor((pc - R) / sp); k <= Math.ceil((pc + R) / sp); k++) {
    if (k === 0) continue;
    const ox = -U[1] * k * sp + L0[0], oy = U[0] * k * sp + L0[1];
    g.moveTo(ox + U[0] * (sc - R), oy + U[1] * (sc - R)); g.lineTo(ox + U[0] * (sc + R), oy + U[1] * (sc + R));
  }
  g.stroke();
  // parallel to the roof
  const qc = (cam.x - L0[0]) * NV[0] + (cam.y - L0[1]) * NV[1];
  const rc = (cam.x - L0[0]) * RV[0] + (cam.y - L0[1]) * RV[1];
  g.strokeStyle = colB; g.beginPath();
  for (let k = Math.floor((qc - R) / sp); k <= Math.ceil((qc + R) / sp); k++) {
    const ox = NV[0] * k * sp + L0[0], oy = NV[1] * k * sp + L0[1];
    g.moveTo(ox + RV[0] * (rc - R), oy + RV[1] * (rc - R)); g.lineTo(ox + RV[0] * (rc + R), oy + RV[1] * (rc + R));
  }
  g.stroke();
}
function pop(cx, cy, p, fn, s0 = 0.86) {
  if (p <= 0) return;
  g.save(); g.translate(cx, cy); const s = lerp(s0, 1, p); g.scale(s, s); g.translate(-cx, -cy);
  g.globalAlpha *= clamp(p * 2.4); fn(); g.restore();
}
function cardBox(x, y, w, h, r = 28, fill = '#fff') {
  g.save();
  g.shadowColor = 'rgba(16,33,58,.16)'; g.shadowBlur = 50; g.shadowOffsetY = 22;
  rr(g, x, y, w, h, r); g.fillStyle = fill; g.fill();
  g.restore();
  rr(g, x, y, w, h, r); g.strokeStyle = 'rgba(16,33,58,.06)'; g.lineWidth = 1.5; g.stroke();
}
function star(ctx, x, y, r, style) {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + (i * Math.PI) / 5, rr2 = i % 2 ? r * 0.46 : r; ctx.lineTo(x + Math.cos(a) * rr2, y + Math.sin(a) * rr2); }
  ctx.closePath(); ctx.fillStyle = style; ctx.fill();
}
function bar(x, y, w, h, style) { rr(g, x, y, w, h, h / 2); g.fillStyle = style; g.fill(); }
// two-point path with ease
function path2(τ, t0, d, a, b, ease = E.inOutCubic) { const p = ease(pr(τ, t0, t0 + d)); return [lerp(a[0], b[0], p), lerp(a[1], b[1], p)]; }

function roleText(τ, idx, en, title, tasks) {
  const s = τ - 0.1;
  txt(g, '0' + idx, -820, -338, { w: 800, size: 30, ls: 1, color: C.blue, t: s, st: 0.04 });
  g.save(); g.globalAlpha = an(s, 0.05, 0.5) * 0.35; seg(g, -770, -349, -770 + 44 * an(s, 0.05, 0.6), -349, C.navy, 2, 'butt'); g.restore();
  txt(g, en, -708, -340, { w: 700, size: 21, ls: 5.5, color: C.mute, t: s - 0.06, st: 0.012 });
  txt(g, title, -826, -196, { w: 900, size: 116, color: C.navy, t: s - 0.05, st: 0.042, d: 0.85 });
  let x = -820;
  for (let i = 0; i < tasks.length; i++) {
    const tt = s - 0.36 - i * 0.1;
    const w = txt(g, tasks[i], x, -112, { w: 500, size: 33, ls: 1, color: C.soft, t: tt, st: 0.018, d: 0.6 });
    x += w + 20;
    if (i < tasks.length - 1) { g.save(); g.globalAlpha = an(tt, 0.12, 0.4); fillPoly(g, towerPts(x, -108, 5, 20), C.blue); g.restore(); x += 25; }
  }
}
function pillBtn(x, y, w, h, o) {      // o: {fill, stroke, color, text, size, icon}
  rr(g, x, y, w, h, h / 2);
  if (o.shadow) { g.save(); g.shadowColor = o.shadow; g.shadowBlur = 30; g.shadowOffsetY = 12; g.fillStyle = o.fill; g.fill(); g.restore(); }
  else { g.fillStyle = o.fill; g.fill(); }
  if (o.stroke) { g.strokeStyle = o.stroke; g.lineWidth = 2; g.stroke(); }
}

// ---- 01 revenue manager: every bar is lifted to the line it deserves ----
const V1 = { f: [0.66, 0.82, 0.56, 0.76, 0.52, 0.7, 0.6], base: 430, w: 86 };
function role1(τ) {
  roleText(τ, 1, 'REVENUE MANAGER', '数字收益经理', ['竞品价格对比', '预订进度监测', '多平台改价']);
  const click = 1.25;
  // baseline
  g.save(); g.globalAlpha = an(τ, 0.15, 0.6); seg(g, 0, V1.base + 1, 0 + 800 * an(τ, 0.15, 0.9), V1.base + 1, rgba(C.navy, 0.18), 2, 'butt'); g.restore();
  for (let i = 0; i < 7; i++) {
    const x = 20 + i * 112, target = V1.base - (LINK * x + 30);
    const h0 = target * V1.f[i] * clamp(spring(τ - 0.2 - i * 0.045, 2.4, 0.72), 0, 1.2);
    if (h0 <= 0) continue;
    const up = E.outExpo(pr(τ, click + 0.12 + i * 0.05, click + 0.9 + i * 0.05));
    const h = lerp(h0, target, up);
    if (up > 0) fillPoly(g, towerPts(x, V1.base, V1.w, h), C.blue);
    fillPoly(g, towerPts(x, V1.base, V1.w, Math.min(h0, h)), C.navy);
    // arrival tick on the line
    const k = pr(τ, click + 0.55 + i * 0.05, click + 1.0 + i * 0.05);
    if (k > 0 && k < 1) { g.save(); g.globalAlpha = 1 - k; ring(g, x, LINK * x, 8 + 26 * E.outCubic(k), C.blue, 3); g.restore(); }
  }
  // suggestion pill -> confirmed by a human
  const pp = spring(τ - 0.62, 3, 0.66), done = an(τ, click, 0.3, E.outCubic), press = Math.sin(Math.PI * pr(τ, click - 0.06, click + 0.16));
  const px = -410, py = 300, pw = 318, ph = 76;
  pop(px + pw / 2, py + ph / 2, pp * (1 - 0.05 * press), () => {
    pillBtn(px, py, pw, ph, { fill: mixc('#FFFFFF', C.blue, done), shadow: mixc('#10213A', C.blue, done, lerp(0.16, 0.38, done)) });
    if (done < 1) { g.save(); g.globalAlpha *= 1 - done; rr(g, px, py, pw, ph, ph / 2); g.strokeStyle = rgba(C.blue, 0.35); g.lineWidth = 2; g.stroke(); g.restore(); }
    // icon
    const ix = px + 44, iy = py + ph / 2;
    if (done < 0.5) { g.save(); g.globalAlpha *= 1 - done * 2; fillPoly(g, towerPts(ix - 13, iy + 15, 10, 20), C.blue); fillPoly(g, towerPts(ix + 1, iy + 15, 10, 31), C.blue); g.restore(); }
    else { g.save(); g.globalAlpha *= (done - 0.5) * 2; checkPath(g, ix - 4, iy + 9, 24, pr(τ, click + 0.08, click + 0.4)); g.strokeStyle = '#fff'; g.lineWidth = 5.5; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke(); g.restore(); }
    g.save(); g.globalAlpha *= 1 - done; label(g, '调价建议 · 待确认', px + 74, py + ph / 2 + 1, { w: 700, size: 27, ls: 1, color: C.navy, base: 'middle' }); g.restore();
    g.save(); g.globalAlpha *= done; label(g, '经理已确认 · 执行', px + 74, py + ph / 2 + 1, { w: 700, size: 27, ls: 1, color: '#fff', base: 'middle' }); g.restore();
  });
  const rp = pr(τ, click, click + 0.5);
  if (rp > 0 && rp < 1) { g.save(); g.globalAlpha = (1 - rp) * 0.5; rr(g, px - 26 * rp, py - 26 * rp, pw + 52 * rp, ph + 52 * rp, (ph + 52 * rp) / 2); g.strokeStyle = C.blue; g.lineWidth = 3; g.stroke(); g.restore(); }
  // cursor
  const cp = path2(τ, 0.55, 0.6, [-560, 560], [px + 232, py + 46], E.outQuart), away = path2(τ, click + 0.25, 1.4, [0, 0], [-30, 46], E.outCubic);
  g.save(); g.globalAlpha = an(τ, 0.5, 0.3); cursor(g, cp[0] + away[0], cp[1] + away[1], 1.15, press); g.restore();
}

// ---- 02 guest relations: a low review, a drafted reply, a human confirms ----
function role2(τ) {
  roleText(τ, 2, 'GUEST RELATIONS', '数字宾客关系专员', ['关注宾客反馈', '起草差评回复', '确认后发布']);
  const click = 1.25;
  g.save(); g.translate(-97.5, -130); g.scale(1.25, 1.25);
  // review card
  pop(265, 185, spring(τ - 0.2, 2.8, 0.7), () => {
    cardBox(30, 70, 470, 232);
    circle(g, 82, 124, 25, '#DCE4F5');
    bar(122, 108, 118, 13, '#BFCBE2'); bar(122, 132, 72, 10, '#DCE4F2');
    for (let i = 0; i < 5; i++) {
      const sp = spring(τ - 0.42 - i * 0.05, 3.2, 0.5);
      if (sp <= 0) continue;
      star(g, 70 + i * 40, 184, 15 * Math.min(sp, 1.25), i < 2 ? C.amberDeep : '#DCE3F0');
    }
    bar(54, 218, 380 * an(τ, 0.5, 0.5), 12, '#D3DBEA'); bar(54, 243, 300 * an(τ, 0.56, 0.5), 12, '#D3DBEA'); bar(54, 268, 190 * an(τ, 0.62, 0.5), 12, '#D3DBEA');
  });
  // reply bubble
  const bp = spring(τ - 0.6, 2.6, 0.68), done = an(τ, click, 0.3, E.outCubic), press = Math.sin(Math.PI * pr(τ, click - 0.06, click + 0.16));
  if (bp > 0) {
    g.save(); g.translate((1 - Math.min(bp, 1.1)) * 150, 0); g.globalAlpha = clamp(bp * 2.2);
    g.save(); g.shadowColor = rgba(C.blue, 0.36); g.shadowBlur = 50; g.shadowOffsetY = 24;
    rr(g, 290, 258, 510, 188, [8, 30, 30, 30]); g.fillStyle = C.blue; g.fill(); g.restore();
    // "AI draft" tag
    fillPoly(g, towerPts(322, 311, 8, 18), '#fff');
    label(g, 'AI 回复草稿', 340, 310, { w: 700, size: 22, ls: 2, color: 'rgba(255,255,255,.92)' });
    const ty = (k) => an(τ, 0.84 + k * 0.12, 0.38, E.outCubic);
    bar(322, 332, 440 * ty(0), 12, 'rgba(255,255,255,.9)'); bar(322, 357, 390 * ty(1), 12, 'rgba(255,255,255,.9)'); bar(322, 382, 250 * ty(2), 12, 'rgba(255,255,255,.9)');
    // confirm button
    const bx = 622, by = 386, bw = 152, bh = 46, s = 1 - 0.07 * press;
    g.save(); g.translate(bx + bw / 2, by + bh / 2); g.scale(s, s); g.translate(-(bx + bw / 2), -(by + bh / 2));
    g.globalAlpha *= an(τ, 1.0, 0.3);
    rr(g, bx, by, bw, bh, bh / 2); g.fillStyle = '#fff'; g.fill();
    g.save(); g.globalAlpha *= 1 - done; label(g, '确认发布', bx + bw / 2, by + bh / 2 + 1, { w: 700, size: 22, ls: 1, color: C.blue, align: 'c', base: 'middle' }); g.restore();
    if (done > 0) {
      g.save(); g.globalAlpha *= done;
      checkPath(g, bx + 30, by + 31, 18, pr(τ, click + 0.05, click + 0.35)); g.strokeStyle = C.blue; g.lineWidth = 4.5; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke();
      label(g, '已发布', bx + 60, by + bh / 2 + 1, { w: 700, size: 22, ls: 1, color: C.blue, base: 'middle' }); g.restore();
    }
    g.restore();
    g.restore();
  }
  // the smile from the wordmark
  const sp = spring(τ - click - 0.18, 2.6, 0.5);
  if (sp > 0) {
    const cx = 512, cy = 78, r = 60;
    g.save(); g.translate(cx, cy); g.scale(Math.min(sp, 1.3), Math.min(sp, 1.3)); g.rotate((1 - Math.min(sp, 1)) * -0.5);
    g.save(); g.shadowColor = 'rgba(16,33,58,.3)'; g.shadowBlur = 30; g.shadowOffsetY = 12; circle(g, 0, 0, r, C.navy); g.restore();
    circle(g, -20, -15, 6.5, '#fff'); circle(g, 20, -15, 6.5, '#fff');
    const bb = WM_GLYPHS.smile.bb, k = 68 / (bb[2] - bb[0]);
    g.translate(-34, 6); g.scale(k, k); g.translate(-bb[0], -bb[1]);
    g.fillStyle = C.amber; g.fill(SMILE_PATH, 'evenodd');
    g.restore();
  }
  const cp = path2(τ, 0.7, 0.5, [900, 620], [716, 416], E.outQuart), away = path2(τ, click + 0.25, 1.4, [0, 0], [26, 44], E.outCubic);
  g.save(); g.globalAlpha = an(τ, 0.72, 0.3); cursor(g, cp[0] + away[0], cp[1] + away[1], 1.0, press); g.restore();
  g.restore();
}

// ---- 03 quality inspector: plan, follow up, sign off ----
function role3(τ) {
  roleText(τ, 3, 'QUALITY INSPECTOR', '数字质检主管', ['质检计划与任务', '整改跟进', '验收与统计']);
  const rows = ['客房卫生', '设施设备', '整改复核'], tk = [0.625, 0.9375, 1.25];
  g.save(); g.translate(-97.5, -130); g.scale(1.25, 1.25);
  pop(295, 240, spring(τ - 0.2, 2.8, 0.7), () => {
    cardBox(30, 56, 530, 368);
    label(g, '质检任务', 66, 114, { w: 800, size: 30, ls: 1, color: C.navy });
    const n = tk.filter((x) => τ > x + 0.12).length;
    rr(g, 444, 86, 84, 38, 19); g.fillStyle = '#EEF2FF'; g.fill();
    label(g, n + ' / 3', 486, 106, { w: 800, size: 21, color: C.blue, align: 'c', base: 'middle' });
    seg(g, 62, 142, 528, 142, 'rgba(16,33,58,.08)', 2, 'butt');
    for (let i = 0; i < 3; i++) {
      const y = 168 + i * 80, rp = an(τ, 0.3 + i * 0.07, 0.5), d = an(τ, tk[i], 0.3, E.outCubic), pu = spring(τ - tk[i], 3.4, 0.45);
      g.save(); g.globalAlpha *= rp; g.translate((1 - rp) * 40, 0);
      if (d > 0) { rr(g, 50, y - 4, 490, 68, 16); g.fillStyle = rgba(C.blue, 0.06 * d); g.fill(); }
      const bs = 1 + 0.18 * (Math.min(pu, 1.4) - (pu > 0 ? 1 : 0)) * (d > 0 ? 1 : 0);
      g.save(); g.translate(84, y + 30); g.scale(bs, bs);
      rr(g, -19, -19, 38, 38, 11); g.fillStyle = mixc('#FFFFFF', C.blue, d); g.fill();
      if (d < 1) { g.strokeStyle = rgba('#AEBBD6', 1 - d); g.lineWidth = 2.5; g.stroke(); }
      if (d > 0) { checkPath(g, -4, 9, 20, pr(τ, tk[i] + 0.04, tk[i] + 0.3)); g.strokeStyle = '#fff'; g.lineWidth = 4.6; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke(); }
      g.restore();
      label(g, rows[i], 124, y + 31, { w: 500, size: 29, ls: 1, color: C.navy, base: 'middle' });
      // status
      rr(g, 416, y + 11, 104, 38, 19); g.fillStyle = mixc('#F1F4FA', '#E3ECFF', d); g.fill();
      g.save(); g.globalAlpha *= 1 - d; label(g, '待检', 468, y + 31, { w: 700, size: 20, ls: 1, color: C.mute, align: 'c', base: 'middle' }); g.restore();
      g.save(); g.globalAlpha *= d; label(g, '已通过', 468, y + 31, { w: 700, size: 20, ls: 1, color: C.blue, align: 'c', base: 'middle' }); g.restore();
      g.restore();
    }
  });
  // ring
  const rp2 = spring(τ - 0.36, 2.8, 0.7), cx = 690, cy = 250, R = 80;
  pop(cx, cy, rp2, () => {
    let prog = 0; for (let i = 0; i < 3; i++) prog += an(τ, tk[i], 0.45, E.outCubic) / 3;
    ring(g, cx, cy, R, '#DCE4F5', 17);
    g.lineCap = 'round';
    if (prog > 0.002) ring(g, cx, cy, R, C.blue, 17, -Math.PI / 2, -Math.PI / 2 + TAU * prog);
    const done = spring(τ - 1.5625, 2.8, 0.45);
    if (done > 0) {
      g.save(); g.translate(cx, cy); g.scale(Math.min(done, 1.4), Math.min(done, 1.4));
      circle(g, 0, 0, 58, C.blue);
      checkPath(g, -11, 21, 46, pr(τ, 1.58, 1.9)); g.strokeStyle = '#fff'; g.lineWidth = 11; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke();
      g.restore();
      const k = pr(τ, 1.5625, 2.15); if (k < 1) { g.save(); g.globalAlpha *= (1 - k) * 0.6; ring(g, cx, cy, R + 14 + 50 * E.outCubic(k), C.blue, 3); g.restore(); }
    } else {
      label(g, Math.round(prog * 100) + '%', cx, cy + 2, { w: 800, size: 40, color: C.navy, align: 'c', base: 'middle' });
    }
    txt(g, '验收通过', cx, cy + R + 62, { w: 700, size: 27, ls: 3, color: C.navy, align: 'c', t: τ - 1.62, st: 0.04, d: 0.6 });
  });
  g.restore();
}

// ---- 04 GM's assistant: the morning brief ----
function role4(τ) {
  roleText(τ, 4, "GM'S ASSISTANT", '数字总经理助理', ['每日早安简报', '重点事项与异常提醒']);
  // sunrise over the line
  const sx = 580, rise = an(τ, 0.25, 1.5, E.outQuart), sy = LINK * sx + lerp(170, -28, rise), R = 104;
  g.save();
  g.beginPath(); g.moveTo(-200, LINK * -200 - 3); g.lineTo(1200, LINK * 1200 - 3); g.lineTo(1200, -1200); g.lineTo(-200, -1200); g.closePath(); g.clip();
  const gl = g.createRadialGradient(sx, sy, R * 0.6, sx, sy, R * 3.6);
  gl.addColorStop(0, rgba(C.amber, 0.5 * rise)); gl.addColorStop(1, rgba(C.amber, 0));
  g.fillStyle = gl; g.fillRect(sx - 600, sy - 600, 1200, 1200);
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * TAU + τ * 0.25, r0 = R + 26, r1 = R + 26 + 34 * an(τ, 0.6 + i * 0.02, 0.6);
    g.save(); g.globalAlpha = rise; seg(g, sx + Math.cos(a) * r0, sy + Math.sin(a) * r0, sx + Math.cos(a) * r1, sy + Math.sin(a) * r1, C.amberDeep, 7, 'round'); g.restore();
  }
  const sg = g.createLinearGradient(0, sy - R, 0, sy + R); sg.addColorStop(0, '#FFD27A'); sg.addColorStop(1, '#FFA82E');
  circle(g, sx, sy, R, sg);
  g.restore();
  // brief card
  const rows = ['调价建议', '差评回复', '质检整改', '订单价格异常'], cols = [C.blue, C.amberDeep, C.navy, '#7FA2FF'];
  g.save(); g.translate(-97.5, -130); g.scale(1.25, 1.25);
  pop(310, 240, spring(τ - 0.2, 2.8, 0.7), () => {
    cardBox(30, 50, 560, 384);
    label(g, '早安简报', 66, 110, { w: 800, size: 32, ls: 1, color: C.navy });
    rr(g, 462, 80, 96, 42, 21); g.fillStyle = '#FFF3DC'; g.fill();
    label(g, '08:00', 510, 102, { w: 800, size: 22, color: '#B66A00', align: 'c', base: 'middle' });
    seg(g, 62, 140, 558, 140, 'rgba(16,33,58,.08)', 2, 'butt');
    for (let i = 0; i < 4; i++) {
      const y = 158 + i * 66, rp = an(τ, 0.42 + i * 0.11, 0.55);
      if (rp <= 0) continue;
      g.save(); g.globalAlpha *= rp; g.translate((1 - rp) * 60, 0);
      rr(g, 62, y + 6, 44, 44, 13); g.fillStyle = cols[i]; g.fill();
      fillPoly(g, towerPts(75, y + 40, 8, 16), '#fff'); fillPoly(g, towerPts(86, y + 40, 8, 24), '#fff');
      label(g, rows[i], 126, y + 29, { w: 500, size: 29, ls: 1, color: C.navy, base: 'middle' });
      const d = spring(τ - 0.95 - i * 0.13, 3.2, 0.5);
      if (d > 0) { g.save(); g.translate(532, y + 28); g.scale(Math.min(d, 1.3), Math.min(d, 1.3)); circle(g, 0, 0, 15, '#E3ECFF'); checkPath(g, -3, 6, 13, 1); g.strokeStyle = C.blue; g.lineWidth = 3.6; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke(); g.restore(); }
      g.restore();
    }
  });
  g.restore();
}

let SMILE_PATH = null;
function drawRoles(t, cam) {
  if (!SMILE_PATH) SMILE_PATH = new Path2D(WM_GLYPHS.smile.d);
  setWorld(cam, 1);
  lattice(cam, rgba(C.blue, 0.07), rgba(C.navy, 0.035));
  // the line + stops
  const a = onLine(BOUND[0] - 60), b = onLine(BOUND[1] + 60);
  seg(g, a[0], a[1], b[0], b[1], C.blue, 5, 'butt');
  const fns = [role1, role2, role3, role4];
  for (let i = 0; i < 4; i++) {
    const n = node(i + 1);
    if (Math.hypot(n[0] - cam.x, n[1] - cam.y) > 2600) continue;
    const τ = t - WHIPS[i];
    atNode(i + 1, () => {
      // stop marker
      fns[i](τ);
      const k = spring(τ - 0.1, 3, 0.5), mx = U[0] * -300, my = U[1] * -300;
      circle(g, mx, my, 15 * Math.min(k, 1.5), '#fff'); ring(g, mx, my, 15 * Math.min(k, 1.5), C.blue, 6);
      const rp = pr(τ, 0.1, 0.9); if (rp > 0 && rp < 1) { g.save(); g.globalAlpha = (1 - rp) * 0.5; ring(g, mx, my, 18 + 70 * E.outCubic(rp), C.blue, 3); g.restore(); }
    });
  }
}
