// Converts the SolidWorks tessellation dump (export/parts.json + parts.bin) into a
// compact, meshopt-compressed GLB with one node per component.
import fs from 'node:fs';
import { Document, NodeIO } from '@gltf-transform/core';
import { EXTMeshoptCompression, KHRMeshQuantization } from '@gltf-transform/extensions';
import { meshopt, prune, dedup } from '@gltf-transform/functions';
import { MeshoptSimplifier, MeshoptEncoder } from 'meshoptimizer';

// Usage: node convert.mjs [outPath] [triangleBudget] [exportDir]
const [, , outPath = 'orion.glb', budgetArg = '160000', exportDir = 'export'] = process.argv;
const TRI_BUDGET = Number(budgetArg);

await MeshoptSimplifier.ready;
await MeshoptEncoder.ready;

const parts = JSON.parse(fs.readFileSync(`${exportDir}/parts.json`, 'utf8'));
const bin = fs.readFileSync(`${exportDir}/parts.bin`);
const totalTris = parts.reduce((s, p) => s + p.tris, 0);
console.log(`${parts.length} parts, ${totalTris} tris`);

// SolidWorks MathTransform.ArrayData: [R00 R01 R02 R10 R11 R12 R20 R21 R22 Tx Ty Tz scale ...]
// Points transform as p' = p * R + T (row vector convention).
function xform(xf, x, y, z) {
  const s = xf[12] ?? 1;
  return [
    (x * xf[0] + y * xf[3] + z * xf[6]) * s + xf[9],
    (x * xf[1] + y * xf[4] + z * xf[7]) * s + xf[10],
    (x * xf[2] + y * xf[5] + z * xf[8]) * s + xf[11],
  ];
}

const doc = new Document();
const buffer = doc.createBuffer();
const scene = doc.createScene('Orion');
const materials = new Map();
function materialFor(key) {
  if (!materials.has(key)) {
    const [r, g, b] = key.split(',').map(Number);
    const lin = (c) => Math.pow(c / 255, 2.2);
    materials.set(key, doc.createMaterial(`c_${r}_${g}_${b}`)
      .setBaseColorFactor([lin(r), lin(g), lin(b), 1])
      .setMetallicFactor(0.1)
      .setRoughnessFactor(0.55));
  }
  return materials.get(key);
}

let outTris = 0;
for (const part of parts) {
  // Group triangles by colour, welding identical positions.
  const groups = new Map();
  for (let t = 0; t < part.tris; t++) {
    const base = part.offset + t * 40;
    const key = `${bin[base + 36]},${bin[base + 37]},${bin[base + 38]}`;
    if (!groups.has(key)) groups.set(key, { map: new Map(), pos: [], idx: [] });
    const g = groups.get(key);
    for (let v = 0; v < 3; v++) {
      let x = bin.readFloatLE(base + v * 12);
      let y = bin.readFloatLE(base + v * 12 + 4);
      let z = bin.readFloatLE(base + v * 12 + 8);
      // Tessellation comes out in part space; move it into assembly space.
      if (part.xf.length) [x, y, z] = xform(part.xf, x, y, z);
      const k = `${x.toFixed(6)},${y.toFixed(6)},${z.toFixed(6)}`;
      let i = g.map.get(k);
      if (i === undefined) { i = g.pos.length / 3; g.map.set(k, i); g.pos.push(x, y, z); }
      g.idx.push(i);
    }
  }

  // Small parts keep proportionally more detail so screws/standoffs don't vanish.
  const share = Math.max(part.tris / totalTris, 0.0015);
  const target = Math.max(60, Math.min(part.tris, Math.round(TRI_BUDGET * share)));
  const ratio = target / part.tris;

  const mesh = doc.createMesh(part.name);
  for (const [key, g] of groups) {
    const pos = new Float32Array(g.pos);
    let idx = new Uint32Array(g.idx);
    // Drop degenerate triangles produced by welding.
    const clean = [];
    for (let i = 0; i < idx.length; i += 3) {
      if (idx[i] !== idx[i + 1] && idx[i + 1] !== idx[i + 2] && idx[i] !== idx[i + 2]) clean.push(idx[i], idx[i + 1], idx[i + 2]);
    }
    idx = new Uint32Array(clean);
    if (idx.length === 0) continue;
    if (ratio < 1) {
      const want = Math.max(3, Math.floor((idx.length * ratio) / 3) * 3);
      const [simp] = MeshoptSimplifier.simplify(idx, pos, 3, want, 0.02, ['Prune']);
      if (simp.length >= 3) idx = simp;
    }
    // Compact the vertex buffer to the vertices still referenced.
    const remap = new Map();
    const newPos = [];
    const newIdx = new Uint32Array(idx.length);
    for (let i = 0; i < idx.length; i++) {
      let j = remap.get(idx[i]);
      if (j === undefined) { j = newPos.length / 3; remap.set(idx[i], j); newPos.push(pos[idx[i] * 3], pos[idx[i] * 3 + 1], pos[idx[i] * 3 + 2]); }
      newIdx[i] = j;
    }
    outTris += newIdx.length / 3;
    const prim = doc.createPrimitive()
      .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array(newPos)).setBuffer(buffer))
      .setIndices(doc.createAccessor().setType('SCALAR').setArray(newPos.length / 3 > 65535 ? newIdx : new Uint16Array(newIdx)).setBuffer(buffer))
      .setMaterial(materialFor(key));
    mesh.addPrimitive(prim);
  }
  if (mesh.listPrimitives().length === 0) continue;
  const node = doc.createNode(part.name).setMesh(mesh).setExtras({ name: part.name });
  scene.addChild(node);
}
console.log(`output tris: ${outTris}, materials: ${materials.size}`);

await doc.transform(dedup(), prune(), meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
const io = new NodeIO().registerExtensions([EXTMeshoptCompression, KHRMeshQuantization])
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder });
await io.write(outPath, doc);
console.log(`wrote ${outPath}: ${(fs.statSync(outPath).size / 1024).toFixed(0)} KB`);
