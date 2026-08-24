// D 模型探索：14 向（6 向 + 8 向）
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const K = 2;

const AXIS6 = [
  [1, 0, 0], [-1, 0, 0],
  [0, 1, 0], [0, -1, 0],
  [0, 0, 1], [0, 0, -1],
];

const BODY8 = [
  [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1],
  [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1],
];

const DIR14 = [...AXIS6, ...BODY8];

function keyOf(p) {
  return `${p[0]},${p[1]},${p[2]}`;
}

function fullCubePoints(k) {
  const pts = [];
  for (let x = -k; x <= k; x++) {
    for (let y = -k; y <= k; y++) {
      for (let z = -k; z <= k; z++) {
        pts.push([x, y, z]);
      }
    }
  }
  return pts;
}

function l1FullPoints(R) {
  const pts = [];
  for (let x = -R; x <= R; x++) {
    for (let y = -R; y <= R; y++) {
      for (let z = -R; z <= R; z++) {
        if (Math.abs(x) + Math.abs(y) + Math.abs(z) <= R) {
          pts.push([x, y, z]);
        }
      }
    }
  }
  return pts;
}

function squarePyramidFace(axis, sign) {
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
        pts.push(coord);
      }
    }
  }
  return pts;
}

function sixFullPyramids() {
  const pts = [];
  for (let axis = 0; axis < 3; axis++) {
    for (const sign of [1, -1]) {
      pts.push(...squarePyramidFace(axis, sign));
    }
  }
  return pts;
}

function fullCubePlusPyramids() {
  return fullCubePoints(K).concat(sixFullPyramids());
}

const sets = {
  cube: {
    label: "5×5×5 正方体",
    points: fullCubePoints(K),
    color: 0x111111,
    size: 0.13,
  },
  l1: {
    label: "L1 球 R=6",
    points: l1FullPoints(6),
    color: 0x2255aa,
    size: 0.13,
  },
  l1Small: {
    label: "L1 球 R=4",
    points: l1FullPoints(4),
    color: 0x557722,
    size: 0.14,
  },
  pyramids: {
    label: "立方体+外部金字塔",
    points: fullCubePlusPyramids(),
    color: 0xaa5522,
    size: 0.13,
  },
  core: {
    label: "L1 满度核心 R=3",
    points: l1FullPoints(3),
    color: 0x00aa44,
    size: 0.16,
  },
};

function buildPointCloud(points, color, size) {
  const positions = [];
  points.forEach((p) => positions.push(p[0], p[1], p[2]));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({ color, size, sizeAttenuation: true });
  return new THREE.Points(geo, mat);
}

function buildEdges(points, color, opacity = 0.12) {
  const set = new Set(points.map(keyOf));
  const seen = new Set();
  const positions = [];
  points.forEach((p) => {
    for (const v of DIR14) {
      const q = [p[0] + v[0], p[1] + v[1], p[2] + v[2]];
      if (!set.has(keyOf(q))) continue;
      const a = p < q ? p : q;
      const b = p < q ? q : p;
      const key = `${keyOf(a)}->${keyOf(b)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      positions.push(a[0], a[1], a[2], b[0], b[1], b[2]);
    }
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
  return new THREE.LineSegments(geo, mat);
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(12, 12, 14);

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
  const candidates = [
    ["cube", "show-cube"],
    ["l1", "show-l1"],
    ["l1Small", "show-l1-small"],
    ["pyramids", "show-pyramids"],
    ["core", "show-core"],
  ];

  candidates.forEach(([id, checkId]) => {
    if (!checked(checkId)) return;
    const set = sets[id];
    total += set.points.length;
    content.add(buildPointCloud(set.points, set.color, set.size));
    if (showLines) {
      content.add(buildEdges(set.points, set.color, 0.12));
    }
  });

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
