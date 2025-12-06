
def add_features():
    path = 'dashboard.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add CSS
    # We append it to the existing style block
    css_to_add = """
        .terminal-container {
            background: #1e1e1e;
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-top: 2rem;
            font-family: 'Consolas', 'Monaco', monospace;
            display: none; /* Hidden by default */
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
        }
        .ai-btn:disabled {
            opacity: 0.7;
            cursor: wait;
            background: #4b5563;
            transform: none;
            box-shadow: none;
        }
    """
    
    if '.terminal-container' not in content:
        content = content.replace('</style>', css_to_add + '\n    </style>')

    # 2. Add Button in Header (Handling Whitespace carefully)
    # We look for the refresh button and prepend our AI button
    refresh_btn_part = '<button class="refresh-btn" onclick="loadData()">'
    
    new_btns_html = """<div style="display: flex; gap: 1rem;">
                <button id="aiBtn" class="ai-btn" onclick="runTradingSession()">
                    <span>🤖</span>
                    <span>AI Trading Starten</span>
                </button>
                <button class="refresh-btn" onclick="loadData()">"""
    
    if 'AI Trading Starten' not in content:
        content = content.replace(refresh_btn_part, new_btns_html)
        # We need to close the div after the refresh button closes. 
        # Since replace only touches the start, we need to fix the structure.
        # Actually, let's replace the whole header block if possible, or just wrapping.
        # It's safer to just inject the button BEFORE the refresh button if we don't wrap in a flex div?
        # But header is flex justify-between. 
        # Header currently has H1 and Button.
        # If we add another button, flex justify-between might put H1 left, AI center, Refresh right?
        # Or Just H1 left, and we wrap both buttons in a div on the right.
        
        # Let's replace the closing `</button>` of the refresh button with `</button>\n            </div>`? 
        # No, that's ambiguous.
        
        # Let's try to match the Refresh Button block entirely.
        import re
        btn_regex = r'<button class="refresh-btn" onclick="loadData\(\)">\s*<span>.*?</span>\s*<span>.*?</span>\s*</button>'
        
        replacement = """<div style="display: flex; gap: 1rem; align-items: center;">
                <button id="aiBtn" class="ai-btn" onclick="runTradingSession()">
                    <span>🤖</span>
                    <span>AI Starten</span>
                </button>
                <button class="refresh-btn" onclick="loadData()">
                    <span>🔄</span>
                    <span>Refresh</span>
                </button>
            </div>"""
            
        content = re.sub(btn_regex, replacement, content, flags=re.DOTALL)


    # 3. Add Terminal HTML
    terminal_html = """
        <div id="terminal" class="terminal-container">
            <div class="terminal-header">
                <span class="terminal-title">🖥️ AI Output / System Log</span>
                <button onclick="document.getElementById('terminal').style.display='none'" style="background:none; border:none; color:#888; cursor:pointer; font-size:1.2rem;">&times;</button>
            </div>
            <div id="terminalOutput" class="terminal-content"></div>
        </div>
    """
    
    if 'id="terminal"' not in content:
         # Insert before <script> tag to put it at bottom of body content
         # The content div ends, then script starts.
         # Actually let's put it INSIDE the content div at the bottom? No, outside is better visibility.
         if '<script>' in content:
             content = content.replace('<script>', terminal_html + '\n    <script>')

    # 4. Add JS Function
    js_code = """
        async function runTradingSession() {
            const btn = document.getElementById('aiBtn');
            const term = document.getElementById('terminal');
            const out = document.getElementById('terminalOutput');
            
            if (!confirm('Soll eine neue Trading-Session gestartet werden? Dies wird einige Sekunden dauern.')) return;

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
                    // Auto scroll to bottom
                    out.scrollTop = out.scrollHeight;
                    
                    // Refresh Dashboard Data
                    loadData(); 
                } else {
                    out.innerHTML = '<span style="color: var(--danger); font-weight:bold;">[ERROR] Execution Failed.</span>\\n\\n' + (data.error || data.output);
                }
            } catch (e) {
                out.innerHTML = '<span style="color: var(--danger);">[NETWORK ERROR] Could not contact server. Is run_dashboard.py running?</span>\\n> ' + e;
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        }
    """
    
    if 'async function runTradingSession' not in content:
        # Insert inside script tag, before loadData call
        content = content.replace('// Load data on page load', js_code + '\n        // Load data on page load')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Dashboard upgraded with interactive features.")

if __name__ == '__main__':
    add_features()
