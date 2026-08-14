import { marked } from 'marked'
import hljs from 'highlight.js'
import katex from 'katex'
import DOMPurify from 'dompurify'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'

// marked 配置：代码高亮
marked.setOptions({
  gfm: true,
  breaks: true,
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch {
        return code
      }
    }
    return hljs.highlightAuto(code).value
  },
})

const BLOCK_MATH_RE = /\$\$([\s\S]+?)\$\$/g
const INLINE_MATH_RE = /(?<!\$)\$([^$\n]+?)\$(?!\$)/g

/**
 * 渲染 Markdown + LaTeX
 * 1. 先提取 $$...$$ 块级公式 → KaTeX HTML（占位符保护）
 * 2. 再提取 $...$ 行内公式 → KaTeX HTML
 * 3. 剩余文本交给 marked 渲染
 */
export function renderMarkdown(text) {
  if (!text) return ''
  const placeholders = []

  // 块级公式
  let t = text.replace(BLOCK_MATH_RE, (_m, latex) => {
    const ph = `@@KATEX_BLOCK_${placeholders.length}@@`
    try {
      placeholders.push(katex.renderToString(latex.trim(), { displayMode: true, throwOnError: false }))
    } catch {
      placeholders.push(latex)
    }
    return ph
  })

  // 行内公式
  t = t.replace(INLINE_MATH_RE, (_m, latex) => {
    const ph = `@@KATEX_INLINE_${placeholders.length}@@`
    try {
      placeholders.push(katex.renderToString(latex.trim(), { throwOnError: false }))
    } catch {
      placeholders.push(latex)
    }
    return ph
  })

  let html = marked.parse(t) || ''
  // XSS 防护：marked 15.x 不再自带 sanitize，AI 输出 / 提示词注入的 HTML 一律消毒
  html = DOMPurify.sanitize(html)

  // 还原公式占位符
  placeholders.forEach((v, i) => {
    html = html.replaceAll(`@@KATEX_BLOCK_${i}@@`, `<div class="katex-block">${v}</div>`)
    html = html.replaceAll(`@@KATEX_INLINE_${i}@@`, `<span class="katex-inline">${v}</span>`)
  })

  // 代码块增强：语言徽章 + 复制按钮（消毒与公式还原之后注入，内容已安全）
  html = html.replace(/<pre><code class="([^"]*)">([\s\S]*?)<\/code><\/pre>/g, (_m, cls, code) => {
    const lang = (cls.match(/language-([\w+-]+)/) || [])[1] || 'code'
    const safeLang = lang.replace(/[<>&"]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c]))
    return `<div class="code-block"><div class="code-toolbar"><span class="code-lang">${safeLang}</span><button type="button" class="code-copy">复制</button></div><pre><code class="${cls}">${code}</code></pre></div>`
  })

  return html
}

export default renderMarkdown
