// 主菜单：收集表单配置 -> POST /api/game/new -> 进入游戏页
window.__polyJump = { gameId: null, state: null };

function parseCustomVectors(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const parts = line.split(",").map((s) => parseInt(s.trim(), 10));
      if (parts.length !== 3 || parts.some((v) => Number.isNaN(v))) {
        throw new Error("自定义向量格式错误：" + line);
      }
      return parts;
    });
}

function boardSize() {
  return [
    parseInt(document.getElementById("board-x").value, 10),
    parseInt(document.getElementById("board-y").value, 10),
    parseInt(document.getElementById("board-z").value, 10),
  ];
}

function autoLayers() {
  const [x, y, z] = boardSize();
  const minSide = Math.min(x, y, z);
  // 用户规则：层数 = max(2, floor(最短边 / 2))
  return Math.max(2, Math.floor(minSide / 2));
}

function updateLayers() {
  document.getElementById("layers").value = autoLayers();
}

function updateGeometryFields() {
  const isB = document.getElementById("geometry").value === "B";
  document.getElementById("b-radius-field").classList.toggle("hidden", !isB);
  document.getElementById("layers-field").classList.toggle("hidden", isB);
  document.getElementById("layers-hint").classList.toggle("hidden", isB);
}

function selectedDirections() {
  return Array.from(
    document.querySelectorAll("input[data-dir]:checked")
  ).map((el) => parseInt(el.dataset.dir, 10));
}

function updateDirectionSummary() {
  const dirs = selectedDirections();
  const total = dirs.reduce((sum, d) => sum + d, 0);
  const label = dirs.length ? dirs.join(" + ") : "未选择";
  const text = dirs.length
    ? `当前：${label} = ${total} 向`
    : "请至少选择一种基础方向";
  document.getElementById("direction-summary").textContent = text;
}

function readConfig() {
  const geometry = document.getElementById("geometry").value;
  const dirs = selectedDirections();
  if (geometry === "A" && dirs.length === 0) {
    throw new Error("请至少选择一种基础方向");
  }

  const players = parseInt(document.getElementById("players").value, 10);
  const bRadius = parseInt(document.getElementById("b-radius").value, 10);
  if (geometry === "B" && (bRadius <= 0 || bRadius % 2 !== 0)) {
    throw new Error("B 模型半径必须为正偶数");
  }
  if (geometry === "B" && players === 8) {
    throw new Error("B 模型第一版支持 2 / 3 / 4 / 6 人");
  }

  return {
    game_name: "PolyJump",
    geometry,
    board_size: boardSize(),
    b_radius: bRadius,
    players,
    direction_set: geometry === "B" ? [12] : dirs,
    custom_vectors: geometry === "B" ? [] : parseCustomVectors(document.getElementById("custom-vectors").value),
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
    },
    goal: {
      objective: "FILL_TARGET",
      target_region: "OPPOSITE_CORNER",
      must_fill_all_cells: true,
    },
    initial_layout: {
      shape: "TETRA_PYRAMID",
      layers: parseInt(document.getElementById("layers").value, 10),
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

document.querySelectorAll("input[data-dir]").forEach((el) => {
  el.addEventListener("change", updateDirectionSummary);
});

document.getElementById("geometry").addEventListener("change", () => {
  updateGeometryFields();
  if (document.getElementById("geometry").value === "A") {
    updateLayers();
  }
});

updateGeometryFields();
updateLayers();
updateDirectionSummary();
