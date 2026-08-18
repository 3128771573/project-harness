// 图灵斑图 · Gray-Scott 反应扩散引擎（WebGL2 + 浮点纹理）
// 参考：Alan Turing 1952 反应扩散理论；Pearson 参数化；Karl Sims 实现
// 关键实证结论（CPU 镜像验证）：
//   - 种子区域必须 u=0/v=1（纯噪声或 u=1 种子无法启动反应）
//   - 方向性由种子形状引导：竖长条→竖条纹，横长条→横条纹
//   - du=1.0/dv=0.5 时 f/k 用 Pearson 经典参数即可稳定出图案

export const ANIMALS = [
  { id: 'zebra', name: '斑马', en: 'Zebra', f: 0.0545, k: 0.062, du: 1.0, dv: 0.5, seed: 'stripes-v', threshold: 0.45,
    colors: { a: [0.05, 0.05, 0.06], b: [0.45, 0.45, 0.48], c: [0.94, 0.94, 0.97] } },
  { id: 'leopard', name: '豹', en: 'Leopard', f: 0.026, k: 0.058, du: 1.0, dv: 0.5, seed: 'spots', threshold: 0.5,
    colors: { a: [0.30, 0.16, 0.06], b: [0.62, 0.44, 0.18], c: [0.95, 0.88, 0.70] } },
  { id: 'napoleon', name: '苏眉鱼', en: 'Napoleon Wrasse', f: 0.030, k: 0.062, du: 1.0, dv: 0.5, seed: 'maze', threshold: 0.5,
    colors: { a: [0.04, 0.16, 0.33], b: [0.10, 0.52, 0.55], c: [0.72, 0.92, 0.96] } },
  { id: 'boxfish', name: '箱鲀', en: 'Boxfish', f: 0.0545, k: 0.062, du: 1.0, dv: 0.5, seed: 'grid', threshold: 0.45,
    colors: { a: [0.03, 0.09, 0.27], b: [0.30, 0.42, 0.52], c: [0.93, 0.96, 1.00] } },
  { id: 'tiger', name: '老虎', en: 'Tiger', f: 0.0545, k: 0.062, du: 1.0, dv: 0.5, seed: 'stripes-h', threshold: 0.45,
    colors: { a: [0.10, 0.05, 0.03], b: [0.72, 0.36, 0.08], c: [0.96, 0.85, 0.60] } },
  { id: 'giraffe', name: '长颈鹿', en: 'Giraffe', f: 0.026, k: 0.058, du: 1.0, dv: 0.5, seed: 'spots-big', threshold: 0.5,
    colors: { a: [0.28, 0.16, 0.07], b: [0.55, 0.40, 0.22], c: [0.90, 0.84, 0.70] } },
  { id: 'butterflyfish', name: '蝴蝶鱼', en: 'Butterflyfish', f: 0.030, k: 0.062, du: 1.0, dv: 0.5, seed: 'stripes-diag', threshold: 0.5,
    colors: { a: [0.04, 0.11, 0.28], b: [0.18, 0.42, 0.68], c: [0.95, 0.80, 0.28] } },
]

const SIM_SIZE = 512
// 预模拟步数：du=1.0 时 4000 步后图案基本稳定（CPU 镜像 256² 实证）
const PRESIM_STEPS = 5000

function mulberry32(a) {
  return function () {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// 生成初始浓度纹理（U=1 均匀，V 按动物种子分布；种子区 u=0/v=1 才能启动反应）
function buildSeed(animal) {
  const size = SIM_SIZE
  const n = size * size
  const data = new Float32Array(n * 4)
  const rng = mulberry32(Math.floor(Math.random() * 1e9))
  const type = animal.seed
  const setSeed = (x, y) => {
    const i = (y * size + x) * 4
    data[i] = 0
    data[i + 1] = 1
  }
  for (let i = 0; i < n; i++) {
    data[i * 4] = 1.0
    data[i * 4 + 3] = 1.0
  }
  if (type === 'stripes-v') {
    // 竖细条：宽 6px 间隔 80px（512 网格；256 实证为 3px/40px）
    for (let x = 8; x < size; x += 80) {
      for (let y = 0; y < size; y++) for (let xx = x; xx < Math.min(size, x + 6); xx++) setSeed(xx, y)
    }
  } else if (type === 'stripes-h') {
    for (let y = 8; y < size; y += 80) {
      for (let yy = y; yy < Math.min(size, y + 6); yy++) for (let x = 0; x < size; x++) setSeed(x, yy)
    }
  } else if (type === 'stripes-diag') {
    // 斜向细条
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      if (Math.sin((x + y) * 0.045) > 0.96) setSeed(x, y)
    }
  } else if (type === 'spots' || type === 'maze') {
    const nb = type === 'spots' ? 45 : 35
    for (let b = 0; b < nb; b++) {
      const s = 12 + Math.floor(rng() * 14)
      const x0 = Math.floor(rng() * (size - s)), y0 = Math.floor(rng() * (size - s))
      for (let y = y0; y < y0 + s; y++) for (let x = x0; x < x0 + s; x++) setSeed(x, y)
    }
  } else if (type === 'spots-big') {
    for (let b = 0; b < 22; b++) {
      const s = 22 + Math.floor(rng() * 18)
      const x0 = Math.floor(rng() * (size - s)), y0 = Math.floor(rng() * (size - s))
      for (let y = y0; y < y0 + s; y++) for (let x = x0; x < x0 + s; x++) setSeed(x, y)
    }
  } else if (type === 'grid') {
    // 蜂窝网格种子
    const cell = 32
    for (let gy = 0; gy < size / cell; gy++) {
      for (let gx = 0; gx < size / cell; gx++) {
        const off = gy % 2 === 0 ? 0 : cell / 2
        const cx0 = Math.floor(gx * cell + off), cy0 = Math.floor(gy * cell)
        if (rng() < 0.7) {
          const s = 14
          for (let y = cy0; y < Math.min(size, cy0 + s); y++) for (let x = cx0; x < Math.min(size, cx0 + s); x++) setSeed(x, y)
        }
      }
    }
  }
  return data
}

const VERT = [
  '#version 300 es',
  'layout(location = 0) in vec2 aPos;',
  'out vec2 vUv;',
  'void main() {',
  '  vUv = aPos * 0.5 + 0.5;',
  '  gl_Position = vec4(aPos, 0.0, 1.0);',
  '}',
].join('\n')

const SIM_FRAG = [
  '#version 300 es',
  'precision highp float;',
  'uniform sampler2D uTex;',
  'uniform vec2 uTexel;',
  'uniform float uF;',
  'uniform float uK;',
  'uniform float uDu;',
  'uniform float uDv;',
  'in vec2 vUv;',
  'out vec4 fragColor;',
  'void main() {',
  '  vec4 c = texture(uTex, vUv);',
  '  float u = c.r;',
  '  float v = c.g;',
  '  float lu = 0.0;',
  '  float lv = 0.0;',
  '  for (int dy = -1; dy <= 1; dy++) {',
  '    for (int dx = -1; dx <= 1; dx++) {',
  '      vec2 p = vUv + vec2(float(dx) * uTexel.x, float(dy) * uTexel.y);',
  '      vec4 n = texture(uTex, p);',
  '      float w = (dx == 0 && dy == 0) ? -1.0 : ((abs(dx) + abs(dy)) == 1 ? 0.2 : 0.05);',
  '      lu += w * n.r;',
  '      lv += w * n.g;',
  '    }',
  '  }',
  '  float uvv = u * v * v;',
  '  float u2 = u + uDu * lu - uvv + uF * (1.0 - u);',
  '  float v2 = v + uDv * lv + uvv - (uF + uK) * v;',
  '  fragColor = vec4(clamp(u2, 0.0, 1.0), clamp(v2, 0.0, 1.0), 0.0, 1.0);',
  '}',
].join('\n')

// 用 u 通道渲染（u 对比度强：图案区 u≈0.3，背景 u≈0.9）
const DRAW_FRAG = [
  '#version 300 es',
  'precision highp float;',
  'uniform sampler2D uTex;',
  'uniform vec3 uColA;',
  'uniform vec3 uColB;',
  'uniform vec3 uColC;',
  'uniform float uThreshold;',
  'in vec2 vUv;',
  'out vec4 fragColor;',
  'void main() {',
  '  vec4 c = texture(uTex, vUv);',
  '  float x = clamp((1.0 - c.r) * 1.55, 0.0, 1.0);',
  '  vec3 col;',
  '  if (x < 0.5) {',
  '    col = mix(uColA, uColB, x * 2.0);',
  '  } else {',
  '    col = mix(uColB, uColC, (x - 0.5) * 2.0);',
  '  }',
  '  float boost = smoothstep(uThreshold - 0.15, uThreshold + 0.15, x);',
  '  col = mix(col, boost < 0.5 ? uColA : uColC, 0.6);',
  '  fragColor = vec4(col, 1.0);',
  '}',
].join('\n')

function createProgram(gl, vs, fs) {
  const v = gl.createShader(gl.VERTEX_SHADER)
  gl.shaderSource(v, vs)
  gl.compileShader(v)
  if (!gl.getShaderParameter(v, gl.COMPILE_STATUS)) return null
  const f = gl.createShader(gl.FRAGMENT_SHADER)
  gl.shaderSource(f, fs)
  gl.compileShader(f)
  if (!gl.getShaderParameter(f, gl.COMPILE_STATUS)) return null
  const p = gl.createProgram()
  gl.attachShader(p, v)
  gl.attachShader(p, f)
  gl.linkProgram(p)
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) return null
  return p
}

function createFloatTexture(gl, internal, type) {
  const tex = gl.createTexture()
  gl.bindTexture(gl.TEXTURE_2D, tex)
  gl.texImage2D(gl.TEXTURE_2D, 0, internal, SIM_SIZE, SIM_SIZE, 0, gl.RGBA, type, null)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  gl.bindTexture(gl.TEXTURE_2D, null)
  return tex
}

function createFBO(gl, tex) {
  const fbo = gl.createFramebuffer()
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo)
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0)
  gl.bindFramebuffer(gl.FRAMEBUFFER, null)
  return fbo
}

export function createTuring(canvas) {
  const gl = canvas.getContext('webgl2', { antialias: false, alpha: false })
  if (!gl) return { ok: false, reason: '当前浏览器不支持 WebGL2' }

  let useFloat32 = false
  let useFloat16 = false
  if (gl.getExtension('EXT_color_buffer_float') && gl.getExtension('OES_texture_float_linear')) useFloat32 = true
  else if (gl.getExtension('EXT_color_buffer_half_float')) useFloat16 = true
  if (!useFloat32 && !useFloat16) return { ok: false, reason: '当前设备不支持 GPU 浮点纹理' }

  const internal = useFloat32 ? gl.RGBA32F : gl.RGBA16F
  const type = useFloat32 ? gl.FLOAT : gl.HALF_FLOAT

  const simProg = createProgram(gl, VERT, SIM_FRAG)
  const drawProg = createProgram(gl, VERT, DRAW_FRAG)
  if (!simProg || !drawProg) return { ok: false, reason: '着色器编译失败' }

  const vao = gl.createVertexArray()
  gl.bindVertexArray(vao)
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
  gl.enableVertexAttribArray(0)
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)

  const texA = createFloatTexture(gl, internal, type)
  const texB = createFloatTexture(gl, internal, type)
  const fboA = createFBO(gl, texA)
  const fboB = createFBO(gl, texB)

  let animal = ANIMALS[0]
  let currentTex = texA
  let currentFbo = fboA
  let otherFbo = fboB

  function upload(data) {
    gl.bindTexture(gl.TEXTURE_2D, currentTex)
    gl.texImage2D(gl.TEXTURE_2D, 0, internal, SIM_SIZE, SIM_SIZE, 0, gl.RGBA, type, data)
    gl.bindTexture(gl.TEXTURE_2D, null)
  }

  function passSim() {
    gl.bindFramebuffer(gl.FRAMEBUFFER, otherFbo)
    gl.viewport(0, 0, SIM_SIZE, SIM_SIZE)
    gl.useProgram(simProg)
    gl.bindVertexArray(vao)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, currentTex)
    gl.uniform1i(gl.getUniformLocation(simProg, 'uTex'), 0)
    gl.uniform2f(gl.getUniformLocation(simProg, 'uTexel'), 1 / SIM_SIZE, 1 / SIM_SIZE)
    gl.uniform1f(gl.getUniformLocation(simProg, 'uF'), animal.f)
    gl.uniform1f(gl.getUniformLocation(simProg, 'uK'), animal.k)
    gl.uniform1f(gl.getUniformLocation(simProg, 'uDu'), animal.du)
    gl.uniform1f(gl.getUniformLocation(simProg, 'uDv'), animal.dv)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
    const next = currentTex === texA ? texB : texA
    const nextFbo = currentFbo === fboA ? fboB : fboA
    currentTex = next
    currentFbo = nextFbo
    otherFbo = currentFbo === fboA ? fboB : fboA
  }

  function passDraw() {
    gl.bindFramebuffer(gl.FRAMEBUFFER, null)
    gl.viewport(0, 0, canvas.width, canvas.height)
    gl.useProgram(drawProg)
    gl.bindVertexArray(vao)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, currentTex)
    gl.uniform1i(gl.getUniformLocation(drawProg, 'uTex'), 0)
    gl.uniform3fv(gl.getUniformLocation(drawProg, 'uColA'), animal.colors.a)
    gl.uniform3fv(gl.getUniformLocation(drawProg, 'uColB'), animal.colors.b)
    gl.uniform3fv(gl.getUniformLocation(drawProg, 'uColC'), animal.colors.c)
    gl.uniform1f(gl.getUniformLocation(drawProg, 'uThreshold'), animal.threshold)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
  }

  function setAnimal(index) {
    animal = ANIMALS[index % ANIMALS.length]
    const seed = buildSeed(animal)
    upload(seed)
    for (let i = 0; i < PRESIM_STEPS; i++) {
      passSim()
    }
  }

  function resize(w, h) {
    canvas.width = Math.max(2, Math.floor(w))
    canvas.height = Math.max(2, Math.floor(h))
  }

  return { ok: true, ANIMALS, setAnimal, step: passSim, draw: passDraw, resize, getAnimal: () => animal }
}
