// D 模型探索：修正版外接金字塔 + 14 向（6 向 + 8 向）
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

function correctedExternalPyramidPoints() {
  const pts = fullCubePoints(K);
  const otherAxes = (axis) => [0, 1, 2].filter((i) => i !== axis);
  for (let axis = 0; axis < 3; axis++) {
    for (const sign of [1, -1]) {
      const oa = otherAxes(axis);
      const main1 = sign * (K + 1);
      for (let a = -1; a <= 1; a++) {
        for (let b = -1; b <= 1; b++) {
          const p = [0, 0, 0];
          p[axis] = main1;
          p[oa[0]] = a;
          p[oa[1]] = b;
          pts.push(p);
        }
      }
      const main2 = sign * (K + 2);
      const p = [0, 0, 0];
      p[axis] = main2;
      pts.push(p);
    }
  }
  return pts;
}

const sets = {
  ext: {
    points: correctedExternalPyramidPoints(),
    color: 0xaa5522,
    size: 0.14,
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
  if (checked("show-ext")) {
    const set = sets.ext;
    total += set.points.length;
    content.add(buildPointCloud(set.points, set.color, set.size));
    if (showLines) {
      content.add(buildEdges(set.points, set.color, 0.12));
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
