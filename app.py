"""
Matrix Language Web Server
Serves the web interface and handles code execution via Flask.
"""

import sys
import os

# Add src/ to path so we can import the interpreter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Matrix', 'src'))

from flask import Flask, request, jsonify, render_template_string
from lexer import Lexer, LexerError
from parser import Parser, ParseError
from evaluator import Evaluator, MatrixError

app = Flask(__name__)

# ── HTML Template ─────────────────────────────────────────────────────────────

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Matrix Language</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;700;800&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0a0a0f;
      --surface:   #111118;
      --border:    #2a2a3a;
      --accent:    #00e5ff;
      --accent2:   #7b61ff;
      --success:   #00ffaa;
      --error:     #ff4d6d;
      --text:      #e8e8f0;
      --muted:     #6b6b88;
      --font-mono: 'Space Mono', monospace;
      --font-ui:   'Syne', sans-serif;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-ui);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }

    /* ── Grid background ── */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
      z-index: 0;
    }

    /* ── Header ── */
    header {
      position: relative;
      z-index: 1;
      padding: 28px 40px;
      display: flex;
      align-items: center;
      gap: 16px;
      border-bottom: 1px solid var(--border);
      background: rgba(10,10,15,0.8);
      backdrop-filter: blur(12px);
    }

    .logo-mark {
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
      flex-shrink: 0;
      animation: pulse 3s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }

    .logo-text {
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .logo-version {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--muted);
      border: 1px solid var(--border);
      padding: 2px 8px;
      border-radius: 4px;
      margin-left: 4px;
    }

    .header-right {
      margin-left: auto;
      display: flex;
      gap: 24px;
      align-items: center;
    }

    .badge {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--muted);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .badge-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
      animation: blink 2s ease-in-out infinite;
    }

    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }

    /* ── Main layout ── */
    main {
      position: relative;
      z-index: 1;
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: auto 1fr;
      gap: 0;
      height: calc(100vh - 89px);
    }

    /* ── Toolbar ── */
    .toolbar {
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 24px;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }

    .toolbar-label {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .example-btn {
      font-family: var(--font-mono);
      font-size: 11px;
      background: transparent;
      border: 1px solid var(--border);
      color: var(--muted);
      padding: 5px 12px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .example-btn:hover {
      border-color: var(--accent);
      color: var(--accent);
    }

    .run-btn {
      margin-left: auto;
      font-family: var(--font-ui);
      font-weight: 700;
      font-size: 13px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: #000;
      border: none;
      padding: 9px 28px;
      border-radius: 6px;
      cursor: pointer;
      letter-spacing: 0.5px;
      transition: all 0.2s;
      position: relative;
      overflow: hidden;
    }

    .run-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 20px rgba(0,229,255,0.3);
    }

    .run-btn:active { transform: translateY(0); }

    .run-btn.loading {
      opacity: 0.7;
      cursor: not-allowed;
    }

    /* ── Panels ── */
    .panel {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .panel-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 20px;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
      flex-shrink: 0;
    }

    .panel-title {
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: var(--muted);
    }

    .panel-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .panel-dot.blue  { background: var(--accent2); }
    .panel-dot.cyan  { background: var(--accent); }

    .editor-panel { border-right: 1px solid var(--border); }

    /* ── Editor ── */
    #editor {
      flex: 1;
      width: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 14px;
      line-height: 1.7;
      padding: 24px;
      border: none;
      resize: none;
      outline: none;
      tab-size: 4;
      caret-color: var(--accent);
    }

    #editor::selection {
      background: rgba(0,229,255,0.15);
    }

    /* ── Output ── */
    #output-panel {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      font-family: var(--font-mono);
      font-size: 14px;
      line-height: 1.7;
      background: var(--bg);
    }

    #output-panel::-webkit-scrollbar { width: 6px; }
    #output-panel::-webkit-scrollbar-track { background: transparent; }
    #output-panel::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

    .output-placeholder {
      color: var(--muted);
      font-style: italic;
      font-size: 13px;
    }

    .output-line {
      color: var(--success);
      white-space: pre-wrap;
      word-break: break-all;
    }

    .output-error {
      color: var(--error);
      white-space: pre-wrap;
      word-break: break-all;
    }

    .output-meta {
      color: var(--muted);
      font-size: 11px;
      margin-top: 16px;
      padding-top: 12px;
      border-top: 1px solid var(--border);
    }

    /* ── Footer ── */
    footer {
      position: relative;
      z-index: 1;
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 24px;
      border-top: 1px solid var(--border);
      background: var(--surface);
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--muted);
    }

    .kbd {
      background: var(--border);
      padding: 2px 6px;
      border-radius: 3px;
      color: var(--text);
    }
  </style>
</head>
<body>

<header>
  <div class="logo-mark"></div>
  <span class="logo-text">Matrix</span>
  <span class="logo-version">v1.0</span>
  <div class="header-right">
    <span class="badge"><span class="badge-dot"></span> Interpreter Online</span>
  </div>
</header>

<main>
  <!-- Toolbar -->
  <div class="toolbar">
    <button class="run-btn" id="run-btn" onclick="runCode()">▶ Run</button>
  </div>

  <!-- Editor Panel -->
  <div class="panel editor-panel">
    <div class="panel-header">
      <div class="panel-dot blue"></div>
      <span class="panel-title">matrix_program.ml</span>
    </div>
    <textarea id="editor" spellcheck="false" placeholder="# Write your Matrix code here...
x = 5;
print x;">x = 10;
y = 20;
result = x + y;
print result;</textarea>
  </div>

  <!-- Output Panel -->
  <div class="panel">
    <div class="panel-header">
      <div class="panel-dot cyan"></div>
      <span class="panel-title">Output</span>
    </div>
    <div id="output-panel">
      <span class="output-placeholder">Run your program to see output here...</span>
    </div>
  </div>
</main>

<footer>
  <span>Matrix Language Interpreter &mdash; CSC321</span>
  <span>Press <span class="kbd">Ctrl</span> + <span class="kbd">Enter</span> to run</span>
</footer>

<script>
  const examples = {
    hello: `# Hello World in Matrix
message = "Hello, Matrix World!";
print message;`,

    math: `# Math operations
x = 10;
y = 3;

# Integer division and remainder
quotient = x // y;
remainder = x % y;

# Power
squared = x ** 2;

print quotient;
print remainder;
print squared;

# Type conversion
f = float(x);
print f;`,

    function: `# Functions in Matrix
function factorial(n) {
    if (n == 0) {
        return 1;
    }
    result = n * factorial(n - 1);
    return result;
}

print factorial(5);
print factorial(0);`,

    class: `# Classes in Matrix
class Rectangle {
    function area(w, h) {
        return w * h;
    }
    function perimeter(w, h) {
        return 2 * (w + h);
    }
}

r = Rectangle();
a = r.area(5, 3);
p = r.perimeter(5, 3);
print a;
print p;`,

    module: `# Modules in Matrix
module MathUtils {
    function square(n) {
        return n * n;
    }
    function cube(n) {
        return n * n * n;
    }
    function abs_val(n) {
        if (n < 0) {
            return 0 - n;
        }
        return n;
    }
}

print MathUtils.square(4);
print MathUtils.cube(3);
print MathUtils.abs_val(0 - 7);`,

    loop: `# Loops and arrays in Matrix
arr = [1, 2, 3, 4, 5];

# Print array elements by index
i = 0;
while (i < 5) {
    print arr[i];
    i = i + 1;
}

# Countdown with break
x = 10;
while (x > 0) {
    print x;
    if (x == 7) {
        break;
    }
    x = x - 1;
}`,

    errors: `# Matrix strict error examples
# Uncomment one at a time to see errors:

# Type error: cannot mix int and float
# x = 5 + 3.14;

# Immutability: cannot reassign
# y = 10;
# y = 20;

# Division by zero
# z = 10 / 0;

# Undefined variable
# print undefined_var;

# Wrong argument count
function add(a, b) { return a + b; }
# result = add(1, 2, 3);

# This works fine:
result = add(3, 4);
print result;`
  };

  function loadExample(name) {
    document.getElementById('editor').value = examples[name];
    document.getElementById('output-panel').innerHTML =
      '<span class="output-placeholder">Run your program to see output here...</span>';
  }

  async function runCode() {
    const code = document.getElementById('editor').value.trim();
    const btn  = document.getElementById('run-btn');
    const out  = document.getElementById('output-panel');

    if (!code) {
      out.innerHTML = '<span class="output-error">No code to run.</span>';
      return;
    }

    btn.textContent = '⏳ Running...';
    btn.classList.add('loading');
    btn.disabled = true;

    const start = Date.now();

    try {
      const resp = await fetch('/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });

      const data  = await resp.json();
      const elapsed = Date.now() - start;

      if (data.error) {
        out.innerHTML = `<span class="output-error">${escapeHtml(data.error)}</span>
          <div class="output-meta">Execution failed &mdash; ${elapsed}ms</div>`;
      } else if (data.output === '') {
        out.innerHTML = `<span class="output-placeholder">(no output)</span>
          <div class="output-meta">Completed successfully &mdash; ${elapsed}ms</div>`;
      } else {
        const lines = data.output.split('\\n').map(l =>
          `<div class="output-line">${escapeHtml(l)}</div>`
        ).join('');
        out.innerHTML = lines +
          `<div class="output-meta">Completed successfully &mdash; ${elapsed}ms</div>`;
      }
    } catch (e) {
      out.innerHTML = `<span class="output-error">Network error: could not reach the interpreter.</span>`;
    }

    btn.textContent = '▶ Run';
    btn.classList.remove('loading');
    btn.disabled = false;
  }

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // Ctrl+Enter to run
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runCode();
    }
  });

  // Tab key inserts spaces in editor
  document.getElementById('editor').addEventListener('keydown', e => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const ta  = e.target;
      const s   = ta.selectionStart;
      ta.value  = ta.value.substring(0, s) + '    ' + ta.value.substring(ta.selectionEnd);
      ta.selectionStart = ta.selectionEnd = s + 4;
    }
  });
</script>
</body>
</html>'''


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/run', methods=['POST'])
def run_code():
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({'error': 'No code provided'}), 400

    code = data['code']

    try:
        lexer  = Lexer(code)
        tokens = lexer.tokenize()
    except LexerError as e:
        return jsonify({'error': f'Lexer Error: {e}'})

    try:
        parser = Parser(tokens)
        ast    = parser.parse_program()
    except ParseError as e:
        return jsonify({'error': f'Parse Error: {e}'})

    try:
        evaluator = Evaluator()
        output    = evaluator.run(ast)
        return jsonify({'output': output})
    except MatrixError as e:
        return jsonify({'error': f'Runtime Error: {e}'})
    except Exception as e:
        return jsonify({'error': f'Internal Error: {e}'})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Matrix Language Interpreter")
    print("Running at http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
