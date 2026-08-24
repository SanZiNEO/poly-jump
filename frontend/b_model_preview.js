// B 模型点阵探索页：纯前端可视化，不接后端
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const K = 2; // 5×5×5

const FCC12 = [
  [1, 1, 0], [1, -1, 0], [-1, 1, 0], [-1, -1, 0],
  [1, 0, 1], [1, 0, -1], [-1, 0, 1], [-1, 0, -1],
  [0, 1, 1], [0, 1, -1], [0, -1, 1], [0, -1, -1],
];

function keyOf(p) {
  return `${p[0]},${p[1]},${p[2]}`;
}

function parityPoints(parity) {
  const pts = [];
  for (let x = -K; x <= K; x++) {
    for (let y = -K; y <= K; y++) {
      for (let z = -K; z <= K; z++) {
        if ((x + y + z) % 2 === parity) pts.push([x, y, z]);
      }
    }
  }
  return pts;
}

function squarePyramidFace(axis, sign, parity) {
  const pts = [];
  for (let layer = 1; layer <= 2 * K; layer++) {
    const side = 2 * K + 1 - layer;
    let start, end;
    if (layer === 1) {
      start = -K;
      end = K - 1;
    } else {
      start = -((side - 1) >> 1);
      end = (side - 1) >> 1;
      if (side % 2 === 0) end += 1;
    }
    const otherAxes = [0, 1, 2].filter((i) => i !== axis);
    for (let a = start; a <= end; a++) {
      for (let b = start; b <= end; b++) {
        const coord = [0, 0, 0];
        coord[axis] = sign * (K + layer);
        coord[otherAxes[0]] = a;
        coord[otherAxes[1]] = b;
        if (parity === undefined || (coord[0] + coord[1] + coord[2]) % 2 === parity) {
          pts.push(coord);
        }
      }
    }
  }
  return pts;
}

function sixPyramids(parity) {
  const pts = [];
  for (let axis = 0; axis < 3; axis++) {
    for (const sign of [1, -1]) {
      pts.push(...squarePyramidFace(axis, sign, parity));
    }
  }
  return pts;
}

// 连通优先候选：L1 球内的偶子晶格
// 条件：|x|+|y|+|z| <= R 且 x+y+z 为偶数
function l1EvenPoints(R) {
  const pts = [];
  for (let x = -R; x <= R; x++) {
    for (let y = -R; y <= R; y++) {
      for (let z = -R; z <= R; z++) {
        if (Math.abs(x) + Math.abs(y) + Math.abs(z) <= R && (x + y + z) % 2 === 0) {
          pts.push([x, y, z]);
        }
      }
    }
  }
  return pts;
}

function buildPointCloud(points, color, size) {
  const positions = [];
  points.forEach((p) => positions.push(p[0], p[1], p[2]));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({
    color,
    size,
    sizeAttenuation: true,
  });
  return new THREE.Points(geo, mat);
}

function buildEdges(points, color, opacity = 0.15) {
  const set = new Set(points.map(keyOf));
  const seen = new Set();
  const positions = [];
  points.forEach((p) => {
    FCC12.forEach((v) => {
      const q = [p[0] + v[0], p[1] + v[1], p[2] + v[2]];
      if (!set.has(keyOf(q))) return;
      const a = p < q ? p : q;
      const b = p < q ? q : p;
      const ek = `${keyOf(a)}->${keyOf(b)}`;
      if (seen.has(ek)) return;
      seen.add(ek);
      positions.push(a[0], a[1], a[2], b[0], b[1], b[2]);
    });
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
  return new THREE.LineSegments(geo, mat);
}

function buildCubeWireframe() {
  const corners = [];
  for (const x of [-K, K]) {
    for (const y of [-K, K]) {
      for (const z of [-K, K]) {
        corners.push([x, y, z]);
      }
    }
  }
  const edges = [
    [0, 1], [0, 2], [0, 4], [1, 3], [1, 5], [2, 3],
    [2, 6], [3, 7], [4, 5], [4, 6], [5, 7], [6, 7],
  ];
  const positions = [];
  edges.forEach(([a, b]) => {
    positions.push(...corners[a], ...corners[b]);
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.LineBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.5,
  });
  return new THREE.LineSegments(geo, mat);
}

// 画出与中心立方体同尺寸、六个面各外接一个的立方体线框
function buildArmsWireframe() {
  const edges = [
    [0, 1], [0, 2], [0, 4], [1, 3], [1, 5], [2, 3],
    [2, 6], [3, 7], [4, 5], [4, 6], [5, 7], [6, 7],
  ];
  const positions = [];
  for (const axis of [0, 1, 2]) {
    for (const sign of [1, -1]) {
      const lo = [-K, -K, -K];
      const hi = [K, K, K];
      // 外部立方体与中心立方体共享一个面，正方向从 K 到 3K，负方向从 -3K 到 -K
      lo[axis] = sign > 0 ? K : -(3 * K);
      hi[axis] = sign > 0 ? 3 * K : -K;

      const corners = [];
      for (const x of [lo[0], hi[0]]) {
        for (const y of [lo[1], hi[1]]) {
          for (const z of [lo[2], hi[2]]) {
            corners.push([x, y, z]);
          }
        }
      }
      edges.forEach(([a, b]) => {
        positions.push(...corners[a], ...corners[b]);
      });
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.LineBasicMaterial({
    color: 0x999999,
    transparent: true,
    opacity: 0.35,
  });
  return new THREE.LineSegments(geo, mat);
}

const sets = {
  candidate: {
    label: "L1 球 · 偶子晶格",
    points: l1EvenPoints(6),
    color: 0x111111,
    size: 0.13,
  },
};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);

const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.set(13, 12, 14);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
document.getElementById("preview-scene").appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

scene.add(new THREE.AmbientLight(0xffffff, 0.8));
const dirLight = new THREE.DirectionalLight(0xffffff, 0.7);
dirLight.position.set(10, 10, 10);
scene.add(dirLight);

const content = new THREE.Group();
scene.add(content);

function checked(id) {
  return document.getElementById(id).checked;
}

function rebuild() {
  while (content.children.length) {
    const child = content.children.pop();
    if (child.geometry) child.geometry.dispose();
    if (child.material) child.material.dispose();
  }

  const showLines = checked("show-lines");
  let total = 0;

  if (checked("show-candidate")) {
    const set = sets.candidate;
    total += set.points.length;

    content.add(buildPointCloud(set.points, set.color, set.size));
    if (showLines) {
      content.add(buildEdges(set.points, 0xaaaaaa, 0.12));
    }
  }

  document.getElementById("point-count").textContent = String(total);
}

document.querySelectorAll("input[type='checkbox']").forEach((el) => {
  el.addEventListener("change", rebuild);
});

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

rebuild();
animate();
