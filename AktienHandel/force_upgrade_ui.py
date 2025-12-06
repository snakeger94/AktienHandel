
import re

def force_add():
    path = 'dashboard.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. CSS
    css = """
    <style>
        .terminal-container {
            background: #1e1e1e;
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-top: 2rem;
            font-family: 'Consolas', 'Monaco', monospace;
            display: none; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        .terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #333;
        }
        .terminal-title {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 600;
        }
        .terminal-content {
            color: #d4d4d4;
            white-space: pre-wrap;
            font-size: 0.85rem;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.4;
            background: #111;
            padding: 1rem;
            border-radius: 0.5rem;
        }
        .ai-btn {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .ai-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
            background: linear-gradient(135deg, #fbbf24, #b45309);
            color: white;
        }
        .ai-btn:disabled {
            opacity: 0.7;
            cursor: wait;
            background: #4b5563;
        }
    </style>
    """
    
    if '.terminal-container' not in content:
        content = content.replace('</head>', css + '\n</head>')

    # 2. Button Replacement via Regex to be robust against whitespace
    # Matches the refresh button roughly
    btn_pattern = re.compile(r'<button\s+class="refresh-btn"\s+onclick="loadData\(\)"\s*>\s*<span>.*?</span>\s*<span>.*?</span>\s*</button>', re.DOTALL)
    
    new_buttons = """
            <div style="display: flex; gap: 1rem; align-items: center;">
                <button id="aiBtn" class="ai-btn" onclick="runTradingSession()">
                    <span>🤖</span>
                    <span>AI Starten</span>
                </button>
                <button class="refresh-btn" onclick="loadData()">
                    <span>🔄</span>
                    <span>Refresh</span>
                </button>
            </div>
    """
    
    if 'AI Starten' not in content:
        match = btn_pattern.search(content)
        if match:
            content = content[:match.start()] + new_buttons + content[match.end():]
        else:
            print("Warning: Could not find Refresh Button to replace.")

    # 3. Terminal HTML
    term_html = """
        <div id="terminal" class="terminal-container">
            <div class="terminal-header">
                <span class="terminal-title">🖥️ AI Output / System Log</span>
                <button onclick="document.getElementById('terminal').style.display='none'" style="background:none; border:none; color:#888; cursor:pointer; font-size:1.2rem;">&times;</button>
            </div>
            <div id="terminalOutput" class="terminal-content"></div>
        </div>
    """
    
    # We insert this before the closing </div> of the content container, OR just before script
    if 'id="terminal"' not in content:
        # Search for closing body
        content = content.replace('</body>', term_html + '\n</body>')

    # 4. JS Function
    js_code = """
    <script>
        async function runTradingSession() {
            const btn = document.getElementById('aiBtn');
            const term = document.getElementById('terminal');
            const out = document.getElementById('terminalOutput');
            
            // if (!confirm('Start new Session?')) return;

            btn.disabled = true;
            const originalContent = btn.innerHTML;
            btn.innerHTML = '<span>⏳</span><span>AI arbeitet...</span>';
            
            term.style.display = 'block';
            out.innerHTML = '<span style="color: #888;">> Initializing AI System...\\n> Please wait, analyzing market data...</span>';
            
            try {
                const response = await fetch('/api/run_trading', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    out.innerHTML = '<span style="color: var(--success); font-weight:bold;">[SUCCESS] Session Completed.</span>\\n\\n' + data.output;
                    out.scrollTop = out.scrollHeight;
                    loadData(); 
                } else {
                    out.innerHTML = '<span style="color: var(--danger); font-weight:bold;">[ERROR] Execution Failed.</span>\\n\\n' + (data.error || data.output);
                }
            } catch (e) {
                out.innerHTML = '<span style="color: var(--danger);">[NETWORK ERROR] Check Server Console.</span>\\n> ' + e;
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        }
    </script>
    """
    
    if 'async function runTradingSession' not in content:
        content = content.replace('</body>', js_code + '\n</body>')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Force upgrade complete.")

if __name__ == '__main__':
    force_add()
