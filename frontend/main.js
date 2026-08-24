// 游戏页面：Three.js 3D 棋盘渲染 + 交互
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { translations, getCurrentLang } from "./i18n.js";

const state = {
  gameId: null,
  board: null,
  selected: null,
  legalPaths: [],
  scene: null,
  camera: null,
  renderer: null,
  controls: null,
  pointGroup: null,
  pieceGroup: null,
  routeGroup: null,
  highlightGroup: null,
  interactedMeshes: [],
  raycaster: new THREE.Raycaster(),
  pointer: new THREE.Vector2(),
  downPos: null,
  cameraInitialized: false,
  historyData: null,
  replayStep: null,
  replayMode: false,
  replayTimer: null,
  replayControlsAttached: false,
  aiPlayers: new Set(),
  aiMoveTimer: null,
  animationEnabled: true,
  animationSpeed: 0.25,
  animationGroup: null,
};

const PLAYER_COLORS = {
  1: 0xe74c3c,
  2: 0x3498db,
  3: 0x2ecc71,
  4: 0xf1c40f,
  5: 0x9b59b6,
  6: 0xe67e22,
  7: 0x1abc9c,
  8: 0xff69b4,
};

// 棋盘背景/点保持黑白；网格线用极淡灰 + 轻微方向色差
const ROUTE_COLORS = {
  axis6: 0xc3cdd8,
  face12: 0xc3d8c3,
  body8: 0xd2c3d8,
  custom: 0xd8cfc3,
};

function keyOf(pos) {
  return `${pos[0]},${pos[1]},${pos[2]}`;
}

function parseKey(key) {
  return key.split(",").map(Number);
}

function clearGroup(group) {
  if (!group) return;
  while (group.children.length) {
    const child = group.children.pop();
    const idx = state.interactedMeshes.indexOf(child);
    if (idx >= 0) state.interactedMeshes.splice(idx, 1);
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
      else child.material.dispose();
    }
  }
}

function setupRenderer() {
  const container = document.getElementById("scene-container");
  container.innerHTML = "";

  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    powerPreference: "high-performance",
  });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);

  const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  );
  camera.position.set(12, 12, 12);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.target.set(0, 0, 0);

  const ambient = new THREE.AmbientLight(0xffffff, 0.6);
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(10, 20, 10);
  scene.add(ambient, dirLight);

  const pointGroup = new THREE.Group();
  const pieceGroup = new THREE.Group();
  const routeGroup = new THREE.Group();
  const highlightGroup = new THREE.Group();
  scene.add(pointGroup, pieceGroup, routeGroup, highlightGroup);

  state.scene = scene;
  state.camera = camera;
  state.renderer = renderer;
  state.controls = controls;
  state.pointGroup = pointGroup;
  state.pieceGroup = pieceGroup;
  state.routeGroup = routeGroup;
  state.highlightGroup = highlightGroup;

  window.addEventListener("resize", onResize);
  renderer.domElement.addEventListener("pointerdown", onPointerDown);
  renderer.domElement.addEventListener("pointerup", onPointerUp);
}

function onResize() {
  if (!state.renderer) return;
  state.camera.aspect = window.innerWidth / window.innerHeight;
  state.camera.updateProjectionMatrix();
  state.renderer.setSize(window.innerWidth, window.innerHeight);
}

function boardCenter(board) {
  const points = board.points || [];
  if (points.length === 0) return [0, 0, 0];
  const sum = points.reduce(
    (acc, p) => [acc[0] + p[0], acc[1] + p[1], acc[2] + p[2]],
    [0, 0, 0]
  );
  return sum.map((v) => v / points.length);
}

function centerCameraOn(board) {
  const center = boardCenter(board);
  state.controls.target.set(...center);
  state.camera.position.set(center[0] + 10, center[1] + 10, center[2] + 10);
  state.controls.update();
}

function createPieceMesh(pos, player) {
  const geo = new THREE.SphereGeometry(0.32, 12, 12);
  const color = PLAYER_COLORS[player] || 0xffffff;
  const mat = new THREE.MeshPhongMaterial({ color, emissive: color, emissiveIntensity: 0.15 });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(pos[0], pos[1], pos[2]);
  mesh.userData.pos = pos;
  mesh.userData.kind = "piece";
  mesh.userData.player = player;
  return mesh;
}

let dotTexture = null;
function getDotTexture() {
  if (dotTexture) return dotTexture;
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  ctx.beginPath();
  ctx.arc(32, 32, 30, 0, Math.PI * 2);
  ctx.fillStyle = "#222222";
  ctx.fill();
  dotTexture = new THREE.CanvasTexture(canvas);
  return dotTexture;
}

// 所有空格点合并为单个 THREE.Points，大幅减少 draw call
function buildPointCloud(points, pieces, excludeKeys) {
  const positions = [];
  points.forEach((pos) => {
    const key = keyOf(pos);
    if (pieces && pieces[key] != null) return;
    if (excludeKeys && excludeKeys.has(key)) return;
    positions.push(pos[0], pos[1], pos[2]);
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({
    color: 0x222222,
    size: 0.09,
    sizeAttenuation: true,
    map: getDotTexture(),
    transparent: true,
  });
  return new THREE.Points(geo, mat);
}

// 基地点按玩家颜色渲染，方便在抽象几何中辨认起始区域
function buildBasePointCloud(points, color) {
  const positions = [];
  points.forEach((p) => positions.push(p[0], p[1], p[2]));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({
    color,
    size: 0.12,
    sizeAttenuation: true,
    map: getDotTexture(),
    transparent: true,
    opacity: 0.8,
  });
  return new THREE.Points(geo, mat);
}

// 同类型路线合并为一个 LineSegments，每个方向组只占一次 draw call
function rebuildRoutes(routes) {
  const byType = {};
  routes.forEach((route) => {
    const type = route.type || "custom";
    if (!byType[type]) byType[type] = [];
    byType[type].push(route);
  });

  Object.entries(byType).forEach(([type, list]) => {
    const positions = [];
    list.forEach((route) => {
      positions.push(route.from[0], route.from[1], route.from[2]);
      positions.push(route.to[0], route.to[1], route.to[2]);
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    const mat = new THREE.LineBasicMaterial({
      color: ROUTE_COLORS[type] || 0xcccccc,
      transparent: true,
      opacity: 0.18,
    });
    state.routeGroup.add(new THREE.LineSegments(geo, mat));
  });
}

function renderBoard(board) {
  clearGroup(state.pointGroup);
  clearGroup(state.pieceGroup);
  clearGroup(state.routeGroup);
  clearGroup(state.highlightGroup);

  rebuildRoutes(board.routes || []);

  const bases = board.bases || {};
  const baseKeys = new Set();
  Object.values(bases).forEach((list) => {
    list.forEach((p) => baseKeys.add(keyOf(p)));
  });

  state.pointGroup.add(buildPointCloud(board.points || [], board.pieces, baseKeys));

  Object.entries(bases).forEach(([playerStr, list]) => {
    const player = Number(playerStr);
    const color = PLAYER_COLORS[player] || 0xffffff;
    state.pointGroup.add(buildBasePointCloud(list, color));
  });

  Object.entries(board.pieces || {}).forEach(([key, player]) => {
    const pos = parseKey(key);
    const mesh = createPieceMesh(pos, player);
    state.pieceGroup.add(mesh);
    state.interactedMeshes.push(mesh);
  });

  // 相机只在首次进入对局时居中一次，之后不随回合/移动改变视角。
}

function colorToCss(value) {
  return `#${value.toString(16).padStart(6, "0")}`;
}

function updatePlayerRoster(config, currentPlayer) {
  const roster = document.getElementById("player-roster");
  if (!roster) return;
  roster.innerHTML = "";

  const count = (config && config.players) || 2;
  for (let i = 1; i <= count; i++) {
    const chip = document.createElement("div");
    chip.className = "player-chip" + (i === currentPlayer ? " active" : "");
    const color = colorToCss(PLAYER_COLORS[i] || 0xffffff);
    chip.innerHTML = `<span class="player-dot" style="background:${color}"></span><span>玩家 ${i}</span>`;
    roster.appendChild(chip);
  }
}

function renderScoreBoard(board) {
  const box = document.getElementById("score-board");
  if (!box) return;
  box.innerHTML = "";

  const scores = board.scores || {};
  const temp = board.temp_scores || {};
  const count = (board.config && board.config.players) || 2;
  for (let i = 1; i <= count; i++) {
    const chip = document.createElement("div");
    chip.className = "score-chip";
    chip.textContent = `P${i} ${scores[i] || 0}${temp[i] ? ` (+${temp[i]})` : ""}`;
    box.appendChild(chip);
  }
}

function updateHud(board) {
  const status = document.getElementById("status-text");
  const round = board.round || 1;
  const step = board.step_count || 0;
  if (board.winner) {
    status.textContent = `玩家 ${board.winner} 获胜！`;
  } else {
    status.textContent = `第 ${round} 轮 · 第 ${step} 步 · 当前玩家：${board.current_player} · 点击本方棋子查看合法路径`;
  }
  updatePlayerRoster(board.config, board.current_player);
  renderScoreBoard(board);
}

function boardWithPieces(pieces) {
  const b = { ...state.board };
  b.pieces = pieces;
  return b;
}

function piecesForStep(step) {
  const h = state.historyData;
  if (!h) return {};
  if (step === 0) return { ...h.initial_pieces };
  if (step <= h.snapshots.length) return { ...h.snapshots[step - 1] };
  return { ...h.snapshots[h.snapshots.length - 1] };
}

function renderHistoryList() {
  const list = document.getElementById("history-moves");
  if (!list) return;
  list.innerHTML = "";

  const h = state.historyData;
  if (!h) return;

  const items = [{ step: 0, text: "开局" }];
  h.moves.forEach((m, i) => {
    const pathText = m.path.map((p) => p.join(",")).join(" → ");
    items.push({ step: i + 1, text: `${i + 1}. P${m.player} ${pathText}` });
  });

  items.forEach((item) => {
    const div = document.createElement("div");
    div.className = "move-item" + (state.replayStep === item.step ? " current" : "");
    div.textContent = item.text;
    div.addEventListener("click", () => setReplayStep(item.step));
    list.appendChild(div);
  });
}

function setReplayStep(step) {
  const h = state.historyData;
  if (!h) return;
  const max = h.snapshots.length;
  step = Math.max(0, Math.min(step, max));

  state.replayStep = step;
  state.replayMode = true;
  renderBoard(boardWithPieces(piecesForStep(step)));

  const status = document.getElementById("status-text");
  if (step === 0) status.textContent = "回放中：开局";
  else if (step === max) status.textContent = `回放中：最后一手 (${max})`;
  else status.textContent = `回放中：第 ${step} 手`;

  renderHistoryList();
}

function stopAutoReplay() {
  if (state.replayTimer) {
    clearInterval(state.replayTimer);
    state.replayTimer = null;
  }
  const btn = document.getElementById("replay-auto");
  if (btn) btn.textContent = translations[getCurrentLang()].replay_auto;
}

function startAutoReplay() {
  stopAutoReplay();
  const h = state.historyData;
  if (!h) return;
  let step = state.replayStep ?? 0;
  state.replayTimer = setInterval(() => {
    if (step >= h.snapshots.length) {
      stopAutoReplay();
      return;
    }
    step += 1;
    setReplayStep(step);
  }, 800);
  const btn = document.getElementById("replay-auto");
  if (btn) btn.textContent = translations[getCurrentLang()].replay_stop;
}

async function loadHistory(gameId) {
  const res = await fetch(`/api/game/${gameId}/history`);
  if (!res.ok) return;
  state.historyData = await res.json();
  renderHistoryList();
}

function attachReplayControls() {
  document.getElementById("replay-start").addEventListener("click", () => setReplayStep(0));
  document.getElementById("replay-prev").addEventListener("click", () => setReplayStep((state.replayStep ?? 1) - 1));
  document.getElementById("replay-next").addEventListener("click", () => setReplayStep((state.replayStep ?? -1) + 1));
  document.getElementById("replay-end").addEventListener("click", () => setReplayStep(state.historyData ? state.historyData.snapshots.length : 0));
  document.getElementById("replay-auto").addEventListener("click", () => {
    if (state.replayTimer) stopAutoReplay();
    else startAutoReplay();
  });
  document.getElementById("ai-move-btn").addEventListener("click", handleAiMove);
  document.getElementById("anim-enabled").addEventListener("change", (e) => {
    state.animationEnabled = e.target.checked;
  });
  document.getElementById("anim-speed").addEventListener("change", (e) => {
    state.animationSpeed = parseFloat(e.target.value);
  });
}

function clearHighlights() {
  clearGroup(state.highlightGroup);
}

function highlightPaths(paths) {
  clearHighlights();
  paths.forEach((path) => {
    const points = path.map((p) => new THREE.Vector3(...p));
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineBasicMaterial({
      color: 0x111111,
      transparent: true,
      opacity: 0.9,
    });
    state.highlightGroup.add(new THREE.Line(geo, mat));

    const end = path[path.length - 1];
    const endMesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.22, 12, 12),
      new THREE.MeshBasicMaterial({ color: 0x111111 })
    );
    endMesh.position.set(end[0], end[1], end[2]);
    endMesh.userData.pos = end;
    endMesh.userData.kind = "destination";
    state.highlightGroup.add(endMesh);
    state.interactedMeshes.push(endMesh);
  });
}

async function loadLegalPathsFor(pos) {
  const gameId = state.gameId;
  const res = await fetch(
    `/api/game/${gameId}/legal-moves?piece=${keyOf(pos)}`
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "获取合法路径失败");
  }
  const data = await res.json();
  return data.paths;
}

async function selectPiece(pos) {
  state.selected = pos;
  clearHighlights();
  try {
    const paths = await loadLegalPathsFor(pos);
    state.legalPaths = paths;
    highlightPaths(paths);
  } catch (e) {
    console.error(e);
  }
}

async function submitMove(path) {
  const res = await fetch(`/api/game/${state.gameId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    console.error(data.error || data.detail);
    return;
  }
  state.selected = null;
  state.legalPaths = [];
  state.replayMode = false;
  state.replayStep = null;
  stopAutoReplay();

  // 先让当前棋子本身沿路径移动动画
  const lastMove = data.state.history[data.state.history.length - 1];
  await playMoveAnimation(path, lastMove ? lastMove.player : data.state.current_player);

  // 动画结束后再切到最终局面
  state.board = data.state;
  renderBoard(state.board);
  updateHud(state.board);
  await loadHistory(state.gameId);
  renderAiPlayerControls();
  maybeAutoMove();
}

async function handleAiMove() {
  if (state.replayMode) return;
  const res = await fetch(`/api/game/${state.gameId}/ai-move`, {
    method: "POST",
  });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    console.error(data.error || data.detail);
    return;
  }

  state.selected = null;
  state.legalPaths = [];
  state.replayMode = false;
  state.replayStep = null;
  stopAutoReplay();

  const lastMove = data.state.history[data.state.history.length - 1];
  await playMoveAnimation(data.move || [], lastMove ? lastMove.player : data.state.current_player);

  state.board = data.state;
  renderBoard(state.board);
  updateHud(state.board);
  await loadHistory(state.gameId);
  maybeAutoMove();
}

function clearMoveAnimation() {
  if (state.animationGroup) {
    state.scene.remove(state.animationGroup);
    while (state.animationGroup.children.length) {
      const child = state.animationGroup.children.pop();
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
    }
    state.animationGroup = null;
  }
}

function playMoveAnimation(path, player) {
  return new Promise((resolve) => {
    if (!state.animationEnabled || !state.scene || !path || path.length < 2) {
      resolve();
      return;
    }
    clearMoveAnimation();

    // 找到当前棋盘上位于起点的棋子 mesh
    const startKey = keyOf(path[0]);
    const mesh = state.pieceGroup.children.find(
      (m) => m.userData.kind === "piece" && keyOf(m.userData.pos) === startKey
    );
    if (!mesh) {
      resolve();
      return;
    }

    // 高亮路径线（白色背景用黑色高亮）
    const group = new THREE.Group();
    state.animationGroup = group;
    state.scene.add(group);
    const linePts = path.map((p) => new THREE.Vector3(p[0], p[1], p[2]));
    const lineGeo = new THREE.BufferGeometry().setFromPoints(linePts);
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x111111,
      transparent: true,
      opacity: 0.95,
    });
    group.add(new THREE.Line(lineGeo, lineMat));

    // 按空间弧长固定移动速度
    const segLen = [];
    const cum = [0];
    let totalLen = 0;
    for (let i = 0; i < path.length - 1; i++) {
      const a = path[i];
      const b = path[i + 1];
      const l = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
      segLen.push(l);
      totalLen += l;
      cum.push(totalLen);
    }

    const duration = Math.max(0.05, totalLen * state.animationSpeed) * 1000;
    const start = performance.now();

    function pointAt(target) {
      let idx = 0;
      while (idx < segLen.length - 1 && target > cum[idx + 1]) idx++;
      const segStart = cum[idx];
      const segEnd = cum[idx + 1];
      const frac = segEnd > segStart ? (target - segStart) / (segEnd - segStart) : 0;
      const a = path[idx];
      const b = path[idx + 1];
      return [
        a[0] + (b[0] - a[0]) * frac,
        a[1] + (b[1] - a[1]) * frac,
        a[2] + (b[2] - a[2]) * frac,
      ];
    }

    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const pos = pointAt(t * totalLen);
      mesh.position.set(pos[0], pos[1], pos[2]);
      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        clearMoveAnimation();
        resolve();
      }
    }

    requestAnimationFrame(tick);
  });
}

function renderAiPlayerControls() {
  const box = document.getElementById("ai-player-controls");
  if (!box) return;
  box.innerHTML = "";

  const count = (state.board && state.board.config && state.board.config.players) || 2;
  for (let i = 1; i <= count; i++) {
    const label = document.createElement("label");
    label.className = "switch-row";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = state.aiPlayers.has(i);
    cb.addEventListener("change", () => {
      if (cb.checked) state.aiPlayers.add(i);
      else state.aiPlayers.delete(i);
      renderAiPlayerControls();
      maybeAutoMove();
    });
    const span = document.createElement("span");
    span.textContent = `P${i} AI`;
    label.appendChild(cb);
    label.appendChild(span);
    box.appendChild(label);
  }
}

function stopAIMove() {
  if (state.aiMoveTimer) {
    clearTimeout(state.aiMoveTimer);
    state.aiMoveTimer = null;
  }
}

function maybeAutoMove() {
  stopAIMove();
  if (state.winner || state.replayMode) return;
  if (!state.aiPlayers.has(state.board.current_player)) return;
  state.aiMoveTimer = setTimeout(async () => {
    state.aiMoveTimer = null;
    await handleAiMove();
  }, 600);
}

function initAIPlayers() {
  state.aiPlayers = new Set((window.__polyJump && window.__polyJump.aiPlayers) || []);
  renderAiPlayerControls();
  maybeAutoMove();
}

function findPathTo(dest) {
  return state.legalPaths.find((p) => keyOf(p[p.length - 1]) === keyOf(dest));
}

function onPointerDown(e) {
  state.downPos = [e.clientX, e.clientY];
}

async function onPointerUp(e) {
  if (state.replayMode) return;
  if (!state.downPos) return;
  const dx = e.clientX - state.downPos[0];
  const dy = e.clientY - state.downPos[1];
  state.downPos = null;
  if (Math.hypot(dx, dy) > 5) return;

  const rect = state.renderer.domElement.getBoundingClientRect();
  state.pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  state.pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  state.raycaster.setFromCamera(state.pointer, state.camera);

  const hits = state.raycaster.intersectObjects(state.interactedMeshes, false);
  if (hits.length === 0) {
    state.selected = null;
    state.legalPaths = [];
    clearHighlights();
    return;
  }

  const hit = hits[0].object;
  const pos = hit.userData.pos;

  if (hit.userData.kind === "destination") {
    const path = findPathTo(pos);
    if (path) submitMove(path);
    return;
  }

  if (hit.userData.kind === "point") {
    state.selected = null;
    state.legalPaths = [];
    clearHighlights();
    return;
  }

  const owner = state.board.pieces[keyOf(pos)];
  if (owner && owner === state.board.current_player) {
    selectPiece(pos);
  }
}

function animate() {
  requestAnimationFrame(animate);
  if (state.controls) state.controls.update();
  if (state.renderer) state.renderer.render(state.scene, state.camera);
}

window.PolyJumpInit = function (gameId, initialBoard) {
  state.gameId = gameId;
  state.board = initialBoard;
  state.selected = null;
  state.legalPaths = [];
  state.replayMode = false;
  state.replayStep = null;
  state.historyData = null;
  setupRenderer();
  renderBoard(state.board);
  centerCameraOn(state.board);
  state.cameraInitialized = true;
  updateHud(state.board);
  if (!state.replayControlsAttached) {
    attachReplayControls();
    state.replayControlsAttached = true;
  }
  initAIPlayers();
  loadHistory(gameId);
  animate();
};

window.PolyJumpDestroy = function () {
  if (state.renderer) {
    state.renderer.dispose();
    const container = document.getElementById("scene-container");
    if (container) container.innerHTML = "";
  }
  state.scene = null;
  state.camera = null;
  state.renderer = null;
  state.controls = null;
  state.gameId = null;
  state.board = null;
  state.cameraInitialized = false;
  state.historyData = null;
  state.replayStep = null;
  state.replayMode = false;
  state.replayControlsAttached = false;
  state.aiPlayers = new Set();
  stopAutoReplay();
  stopAIMove();
  clearMoveAnimation();
};

// 如果主菜单在主脚本就绪前就创建了对局，这里补初始化。
if (window.__pendingInit) {
  const pending = window.__pendingInit;
  window.__pendingInit = null;
  window.PolyJumpInit(pending.gameId, pending.state);
}
