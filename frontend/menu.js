// 主菜单：收集表单配置 -> POST /api/game/new -> 进入游戏页
import { applyLanguage, getCurrentLang, translations } from "./i18n.js";

const AI_TYPE_OPTIONS = ["distance_graph", "distance_euclidean", "distance_chebyshev"];

window.__polyJump = { gameId: null, state: null };

function boardSize() {
  return [
    parseInt(document.getElementById("board-x").value, 10),
    parseInt(document.getElementById("board-y").value, 10),
    parseInt(document.getElementById("board-z").value, 10),
  ];
}

function maxLayers() {
  const [x, y, z] = boardSize();
  const minSide = Math.min(x, y, z);
  return Math.max(2, Math.floor(minSide / 2));
}

function updateLayers() {
  const input = document.getElementById("layers");
  const max = maxLayers();
  input.max = max;
  const current = parseInt(input.value, 10);
  input.value = Number.isNaN(current) ? max : Math.min(Math.max(current, 1), max);
}

function selectedMenuAIPlayers() {
  return Array.from(
    document.querySelectorAll('#ai-player-menu input[data-ai-player]:checked')
  ).map((el) => parseInt(el.dataset.aiPlayer, 10));
}

function selectedMenuAITypes() {
  const map = {};
  document.querySelectorAll("#ai-player-menu select.ai-type-select").forEach((sel) => {
    map[parseInt(sel.dataset.aiPlayer, 10)] = sel.value;
  });
  return map;
}

function createAiTypeSelect(player) {
  const select = document.createElement("select");
  select.className = "ai-type-select";
  select.dataset.aiPlayer = String(player);
  const lang = getCurrentLang();
  for (const value of AI_TYPE_OPTIONS) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = translations[lang]["ai_" + value] || value;
    select.appendChild(opt);
  }
  select.value = "distance_graph";
  return select;
}

function renderAIPlayerMenu() {
  const wrap = document.getElementById("ai-player-menu");
  if (!wrap) return;
  wrap.innerHTML = "";
  const count = parseInt(document.getElementById("players").value, 10);

  for (let i = 1; i <= count; i++) {
    const row = document.createElement("div");
    row.className = "switch-row";
    const label = document.createElement("label");
    label.className = "ai-player-label";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.dataset.aiPlayer = String(i);
    const span = document.createElement("span");
    span.textContent = `P${i} AI`;
    label.appendChild(cb);
    label.appendChild(span);
    row.appendChild(label);
    row.appendChild(createAiTypeSelect(i));
    wrap.appendChild(row);
  }
}

function updatePlayerOptions(isFixedPlayers) {
  const select = document.getElementById("players");
  const current = parseInt(select.value, 10);
  const allowed = isFixedPlayers ? [2, 3, 4, 6] : [2, 3, 4, 6, 8];

  // 如果从 A 的 8 人切到固定玩家数模型，自动落到 6 人
  const next = allowed.includes(current) ? current : allowed[allowed.length - 1];

  select.innerHTML = "";
  allowed.forEach((v) => {
    const option = document.createElement("option");
    option.value = String(v);
    option.textContent = String(v);
    if (v === next) option.selected = true;
    select.appendChild(option);
  });
  renderAIPlayerMenu();
}

function updateGeometryFields() {
  const geometry = document.getElementById("geometry").value;
  const isL1 = geometry === "B" || geometry === "C";
  const isExt = ["A_EXT", "B_EXT", "C_EXT", "D"].includes(geometry);
  // A-ext 方向可配置，其余外接模型方向固定
  const isFixedDirection = isL1 || (isExt && geometry !== "A_EXT");
  const isFixedPlayers = isL1 || isExt;

  document.getElementById("b-radius-field").classList.toggle("hidden", !isL1);
  document.getElementById("ep-side-field").classList.toggle("hidden", !isExt);
  document.getElementById("layers-field").classList.toggle("hidden", isFixedPlayers);
  document.getElementById("layers-hint").classList.toggle("hidden", isFixedPlayers);
  document.getElementById("direction-section").classList.toggle("hidden", isFixedDirection);
  updatePlayerOptions(isFixedPlayers);

  const summary = document.getElementById("direction-summary");
  if (geometry === "B") summary.textContent = "B 模型固定 12 向";
  else if (geometry === "C") summary.textContent = "C 模型固定 20 向";
  else if (geometry === "D") summary.textContent = "D 模型固定 14 向";
  else if (geometry === "B_EXT") summary.textContent = "B-ext 固定 12 向";
  else if (geometry === "C_EXT") summary.textContent = "C-ext 固定 20 向";
  else updateDirectionSummary();
}

function selectedDirections() {
  return Array.from(
    document.querySelectorAll('input[data-type="base"]:checked')
  ).map((el) => parseInt(el.dataset.dir, 10));
}

function selectedCustomVectors() {
  return Array.from(
    document.querySelectorAll('input[data-type="custom"]:checked')
  ).flatMap((el) => JSON.parse(el.dataset.vectors));
}

function selectedCustomNames() {
  return Array.from(
    document.querySelectorAll('input[data-type="custom"]:checked')
  ).map((el) => el.dataset.label);
}

function updateDirectionSummary() {
  const dirs = selectedDirections();
  const customs = selectedCustomNames();
  const parts = [];
  if (dirs.length) parts.push(dirs.join(" + "));
  customs.forEach((name) => parts.push(name));
  const text = parts.length
    ? `当前：${parts.join(" + ")}`
    : "请至少选择一种移动方向";
  document.getElementById("direction-summary").textContent = text;
}

async function loadDirectionSets() {
  const wrap = document.getElementById("direction-checks");
  const summary = document.getElementById("direction-summary");
  try {
    const res = await fetch("/api/direction-sets");
    if (!res.ok) throw new Error("加载方向规则失败");
    const sets = await res.json();
    wrap.innerHTML = "";

    sets.forEach((set) => {
      const label = document.createElement("label");
      label.className = "switch-row";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.dataset.label = set.name;
      if (set.type === "base") {
        cb.dataset.type = "base";
        cb.dataset.dir = set.id;
        // 默认勾选 6 向和 12 向，方便直接开局
        cb.checked = set.id === "6" || set.id === "12";
      } else {
        cb.dataset.type = "custom";
        cb.dataset.vectors = JSON.stringify(set.vectors);
      }

      const span = document.createElement("span");
      span.textContent = set.name;

      label.appendChild(cb);
      label.appendChild(span);
      wrap.appendChild(label);
      cb.addEventListener("change", updateDirectionSummary);
    });

    updateDirectionSummary();
  } catch (e) {
    summary.textContent = e.message;
  }
}

function readConfig() {
  const geometry = document.getElementById("geometry").value;
  const dirs = selectedDirections();
  const customs = selectedCustomVectors();
  if (geometry === "A" && dirs.length === 0 && customs.length === 0) {
    throw new Error("请至少选择一种移动方向");
  }

  const players = parseInt(document.getElementById("players").value, 10);
  const bRadius = parseInt(document.getElementById("b-radius").value, 10);
  const epSide = parseInt(document.getElementById("ep-side").value, 10);
  const isL1 = geometry === "B" || geometry === "C";
  const isExt = ["A_EXT", "B_EXT", "C_EXT", "D"].includes(geometry);
  const isFixed = isL1 || isExt;

  if (isL1 && (bRadius <= 0 || bRadius % 2 !== 0)) {
    throw new Error("L1 球半径必须为正偶数");
  }
  if (isExt && (epSide < 3 || epSide % 2 === 0)) {
    throw new Error("外接金字塔中心边长必须为奇数且 >= 3");
  }
  if (isFixed && players === 8) {
    throw new Error("B/C/D/A-ext 模型支持 2 / 3 / 4 / 6 人");
  }

  const layers = parseInt(document.getElementById("layers").value, 10);
  const layersMax = maxLayers();
  if (geometry === "A" && (layers < 1 || layers > layersMax)) {
    throw new Error(`A 模型棋子层数不能超过 ${layersMax} 层`);
  }

  const fixedDirection =
    geometry === "B" ? [12] :
    geometry === "C" ? [20] :
    geometry === "D" ? [14] :
    geometry === "B_EXT" ? [12] :
    geometry === "C_EXT" ? [20] : null;

  return {
    game_name: "PolyJump",
    geometry,
    board_size: boardSize(),
    b_radius: bRadius,
    c_radius: bRadius,
    ep_side: epSide,
    players,
    direction_set: fixedDirection !== null ? fixedDirection : dirs,
    custom_vectors: fixedDirection !== null ? [] : customs,
    movement: {
      allow_step: document.getElementById("allow-step").checked,
      allow_jump: document.getElementById("allow-jump").checked,
      allow_chain: document.getElementById("allow-chain").checked,
      hop_mode: document.getElementById("hop-mode").value,
      two_step_hop: document.getElementById("allow-two-step").checked,
      max_chain_length: 0,
    },
    capture: {
      mode: document.getElementById("capture-mode").value,
      capture_opponent_only: true,
      mixed_swap: false,
      capture_in_base: document.getElementById("capture-in-base").checked,
    },
    goal: {
      objective: "FILL_TARGET",
      target_region: "OPPOSITE_CORNER",
      must_fill_all_cells: true,
    },
    initial_layout: {
      shape: "TETRA_PYRAMID",
      layers,
    },
    scoring: {
      enabled: document.getElementById("scoring-enabled").checked,
      first_finish_reward: parseInt(document.getElementById("first-finish-reward").value, 10),
      chain_jump_points: parseInt(document.getElementById("chain-jump-points").value, 10),
      chain_temp: document.getElementById("chain-temp").checked,
      chain_max_scoring: parseInt(document.getElementById("chain-max-scoring").value, 10),
      capture_points: parseInt(document.getElementById("capture-points").value, 10),
      target_zone_points: parseInt(document.getElementById("target-zone-points").value, 10),
      survivor_piece_points: parseInt(document.getElementById("survivor-piece-points").value, 10),
    },
  };
}

async function startGame() {
  const errEl = document.getElementById("menu-error");
  errEl.textContent = "";

  let config;
  try {
    config = readConfig();
  } catch (e) {
    errEl.textContent = e.message;
    return;
  }

  try {
    const res = await fetch("/api/game/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "创建对局失败");
    }

    window.__polyJump.gameId = data.game_id;
    window.__polyJump.state = data.state;
    window.__polyJump.aiPlayers = selectedMenuAIPlayers();
    window.__polyJump.aiTypes = selectedMenuAITypes();

    document.getElementById("menu-page").classList.add("hidden");
    document.getElementById("game-page").classList.remove("hidden");

    if (window.PolyJumpInit) {
      window.PolyJumpInit(data.game_id, data.state);
    } else {
      window.__pendingInit = { gameId: data.game_id, state: data.state };
    }
  } catch (e) {
    errEl.textContent = e.message;
  }
}

document.getElementById("start-btn").addEventListener("click", startGame);
document.getElementById("back-btn").addEventListener("click", () => {
  document.getElementById("game-page").classList.add("hidden");
  document.getElementById("menu-page").classList.remove("hidden");
  if (window.PolyJumpDestroy) {
    window.PolyJumpDestroy();
  }
});

["board-x", "board-y", "board-z"].forEach((id) => {
  document.getElementById(id).addEventListener("input", updateLayers);
});

document.getElementById("geometry").addEventListener("change", () => {
  updateGeometryFields();
  if (document.getElementById("geometry").value === "A") {
    updateLayers();
  }
});

document.getElementById("players").addEventListener("change", renderAIPlayerMenu);

document.getElementById("lang-select").addEventListener("change", (e) => {
  applyLanguage(e.target.value);
});

applyLanguage(getCurrentLang());
updateGeometryFields();
updateLayers();
loadDirectionSets();
