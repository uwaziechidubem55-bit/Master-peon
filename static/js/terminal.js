// ===== MASTER PEON REAL TERMINAL =====
// This is a real terminal connected to /bin/sh on the Kali container.
// Everything works: pipes, redirects, git, apt, pip, python, etc.

const Term = (() => {
  const outputEl = () => $('#terminal-output');
  const inputEl = () => $('#terminal-input');

  let commandHistory = [];
  let historyIndex = -1;
  let toolGeneratorsCache = null;
  let terminalOpen = false;

  function init() {
    loadGenerators();

    // Enter to run
    inputEl().addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        runCommand();
      }
      // History: Up/Down
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (commandHistory.length === 0) return;
        historyIndex = Math.min(historyIndex + 1, commandHistory.length - 1);
        inputEl().value = commandHistory[commandHistory.length - 1 - historyIndex];
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (historyIndex <= 0) {
          historyIndex = -1;
          inputEl().value = '';
          return;
        }
        historyIndex--;
        inputEl().value = commandHistory[commandHistory.length - 1 - historyIndex];
      }
      // Ctrl+Space → generators panel
      if (e.ctrlKey && e.key === ' ') {
        e.preventDefault();
        toggleGenerators();
      }
      // Tab completion
      if (e.key === 'Tab') {
        e.preventDefault();
        tabComplete();
      }
    });

    // Run button
    $('#terminal-run').addEventListener('click', runCommand);

    // Clear
    $('#terminal-clear').addEventListener('click', () => {
      outputEl().innerHTML = '';
      writeLine('term-welcome', 'Terminal cleared. Type help for commands.');
    });

    // Toggle generators
    $('#term-toggle-generators').addEventListener('click', toggleGenerators);

    // Generator search
    $('#gen-search').addEventListener('input', filterGenerators);

    // Close
    $('#terminal-close').addEventListener('click', () => {
      $('#terminal-drawer').classList.add('hidden');
      terminalOpen = false;
    });

    // Ctrl+` toggle
    document.addEventListener('keydown', e => {
      if (e.ctrlKey && e.key === '`') {
        e.preventDefault();
        if (terminalOpen) {
          $('#terminal-drawer').classList.add('hidden');
          terminalOpen = false;
        } else {
          openTerminal();
        }
      }
    });

    writeWelcome();
  }

  function openTerminal() {
    $('#terminal-drawer').classList.remove('hidden');
    terminalOpen = true;
    setTimeout(() => inputEl().focus(), 100);
  }

  function writeWelcome() {
    const out = outputEl();
    out.innerHTML = '';
    writeLine('term-banner', '╔══════════════════════════════════════════════════╗');
    writeLine('term-banner', '║        MASTER PEON REAL TERMINAL v1.0           ║');
    writeLine('term-banner', '║     Full shell — /bin/sh on Kali Linux          ║');
    writeLine('term-banner', '╚══════════════════════════════════════════════════╝');
    writeLine('', '');
    writeLine('term-welcome', '  This is a REAL terminal. Everything works:');
    writeLine('term-welcome', '  → git clone, apt install, pip install, python3');
    writeLine('term-welcome', '  → pipes (|), redirects (>), variables ($HOME)');
    writeLine('term-welcome', '  → cd, ls, cat, grep, curl, wget, nmap, sqlmap');
    writeLine('', '');
    writeLine('term-section', '  Commands:');
    writeLine('term-cmd', '    help              Show this help');
    writeLine('term-cmd', '    tools             List your available pentesting tools');
    writeLine('term-cmd', '    generate <tool>   Show command templates');
    writeLine('term-cmd', '    clear             Clear screen');
    writeLine('term-cmd', '    history           Show command history');
    writeLine('', '');
    writeLine('term-section', '  Shortcuts:');
    writeLine('term-cmd', '    Ctrl+`       Toggle terminal');
    writeLine('term-cmd', '    Ctrl+Space   Browse tool command generators');
    writeLine('term-cmd', '    Up/Down      Command history');
    writeLine('term-cmd', '    Tab          Auto-complete');
    writeLine('', '');
    writeLine('term-welcome', '  📋 Click the clipboard icon in the header for tool generators.');
    updatePrompt();
  }

  function writeLine(cls, text) {
    const line = document.createElement('div');
    line.className = 'term-line' + (cls ? ' ' + cls : '');
    line.textContent = text;
    outputEl().appendChild(line);
    outputEl().scrollTop = outputEl().scrollHeight;
  }

  function writeOutput(text, cls) {
    const lines = text.split('\n');
    for (const line of lines) {
      const div = document.createElement('div');
      div.className = 'term-line' + (cls ? ' ' + cls : '');
      div.textContent = line;
      outputEl().appendChild(div);
    }
    outputEl().scrollTop = outputEl().scrollHeight;
  }

  function writeInputLine(cmd) {
    const line = document.createElement('div');
    line.className = 'term-line';
    line.innerHTML = '<span class="term-prompt-inline">peon@kali:~$</span> ' + escapeHtml(cmd);
    outputEl().appendChild(line);
    outputEl().scrollTop = outputEl().scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function updatePrompt() {
    const tier = ($('#u-tier') && $('#u-tier').textContent) || 'free';
    $('#term-prompt').textContent = 'peon@kali:~$';
    $('#term-tier-badge').textContent = '[' + tier.toUpperCase() + ']';
  }

  // ===== RUN COMMAND =====
  async function runCommand() {
    const cmd = inputEl().value.trim();
    if (!cmd) return;
    inputEl().value = '';

    // Add to history
    commandHistory.push(cmd);
    historyIndex = -1;

    // Show input
    writeInputLine(cmd);

    // Built-in commands (client-side only)
    if (cmd === 'clear') {
      outputEl().innerHTML = '';
      writeWelcome();
      return;
    }
    if (cmd === 'help') {
      showHelp();
      return;
    }
    if (cmd === 'history') {
      commandHistory.forEach((c, i) => writeLine('', '  ' + (i+1) + '  ' + c));
      return;
    }
    if (cmd === 'tools' || cmd === 'ls-tools') {
      showTools();
      return;
    }
    if (cmd.startsWith('generate ')) {
      const toolName = cmd.slice(9).trim();
      showToolGenerators(toolName);
      return;
    }

    // Send to backend for real execution
    writeLine('term-info', '⏳ Running...');
    try {
      const r = await Auth.api('/api/terminal/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
      });
      const data = await r.json();

      // Remove "Running..." line
      removeLastLine('⏳ Running...');

      if (data.output) {
        // Color the output based on context
        const cls = data.tool ? 'term-output' : '';
        writeOutput(data.output, cls);
      }
      if (data.exit_code && data.exit_code !== 0) {
        writeLine('term-error', '\n[!] Exit code: ' + data.exit_code);
      }
    } catch (err) {
      removeLastLine('⏳ Running...');
      
      let msg = err.message || 'Request failed';
      if (msg.includes('403')) {
        writeLine('term-error', '[!] Access denied: Tool not available on your tier.');
        writeLine('term-welcome', '    Upgrade your plan or use a different command.');
      } else if (msg.includes('429')) {
        writeLine('term-error', '[!] Daily tool-call limit reached.');
      } else if (msg.includes('400')) {
        writeLine('term-error', '[!] ' + msg.replace('400: ', ''));
      } else {
        writeLine('term-error', '[!] Error: ' + msg);
      }
    }
    outputEl().scrollTop = outputEl().scrollHeight;
  }

  function removeLastLine(textMatch) {
    const lines = outputEl().querySelectorAll('.term-line');
    for (let i = lines.length - 1; i >= 0; i--) {
      if (lines[i].textContent.includes(textMatch)) {
        lines[i].remove();
        break;
      }
    }
  }

  // ===== HELP =====
  async function showHelp() {
    writeLine('term-title', '═══ MASTER PEON REAL TERMINAL HELP ═══');
    writeLine('', '');
    writeLine('term-section', 'Built-in Commands:');
    writeLine('term-cmd', '  clear             Clear terminal screen');
    writeLine('term-cmd', '  help              Show this help');
    writeLine('term-cmd', '  history           Show command history');
    writeLine('term-cmd', '  tools             List available pentesting tools');
    writeLine('term-cmd', '  generate <tool>   Show command templates for a tool');
    writeLine('', '');
    writeLine('term-section', 'General Commands (everything works):');
    writeLine('term-cmd', '  git clone <url>           Clone a repository');
    writeLine('term-cmd', '  apt install <pkg>         Install packages (Pro+)');
    writeLine('term-cmd', '  pip install <pkg>         Install Python packages (Pro+)');
    writeLine('term-cmd', '  python3 <script>          Run Python scripts');
    writeLine('term-cmd', '  curl <url>                Fetch URLs');
    writeLine('term-cmd', '  wget <url>                Download files');
    writeLine('term-cmd', '  ls, cat, grep, find       Standard Linux commands');
    writeLine('term-cmd', '  command1 | command2        Pipes work');
    writeLine('term-cmd', '  command > file             Redirects work');
    writeLine('', '');
    writeLine('term-section', 'Pentesting Tools (tier-dependent):');
    writeLine('term-cmd', '  Type "tools" to see your available tools');
    writeLine('term-cmd', '  Type "generate <tool>" for command templates');
    writeLine('', '');
    writeLine('term-section', 'Shortcuts:');
    writeLine('term-cmd', '  Ctrl+`          Toggle terminal');
    writeLine('term-cmd', '  Ctrl+Space      Browse tool command generators');
    writeLine('term-cmd', '  Up/Down         Command history');
    writeLine('term-cmd', '  Tab             Auto-complete tool names');
  }

  // ===== SHOW TOOLS =====
  async function showTools() {
    writeLine('term-title', '═══ YOUR AVAILABLE PENTESTING TOOLS ═══');
    writeLine('', '');
    try {
      const r = await Auth.api('/api/terminal/tools');
      const data = await r.json();
      writeLine('term-welcome', '  Tier: ' + data.tier.toUpperCase());
      writeLine('term-welcome', '  Tools available: ' + (data.tool_count || 0));
      writeLine('', '');
      const names = Object.keys(data.tools);
      if (names.length === 0) {
        writeLine('term-error', '  No pentesting tools on your current tier.');
        return;
      }
      // Display in columns
      let row = '';
      names.forEach((name, i) => {
        row += name.padEnd(14);
        if ((i + 1) % 5 === 0 || i === names.length - 1) {
          writeLine('term-tool', '  ' + row);
          row = '';
        }
      });
      writeLine('', '');
      writeLine('term-welcome', '  Use "generate <toolname>" for command templates.');
      writeLine('term-welcome', '  Or press Ctrl+Space to browse generators.');
    } catch (err) {
      writeLine('term-error', '  Failed: ' + (err.message || ''));
    }
  }

  // ===== SHOW GENERATORS =====
  async function showToolGenerators(toolName) {
    try {
      const r = await Auth.api('/api/terminal/tools');
      const data = await r.json();
      const info = data.tools[toolName];
      if (!info) {
        writeLine('term-error', '  Tool "' + toolName + '" not found or not on your tier.');
        writeLine('term-welcome', '  Type "tools" to see available tools.');
        return;
      }
      writeLine('term-title', '═══ ' + toolName.toUpperCase() + ' — Command Generators ═══');
      writeLine('', '');
      if (!info.generators || info.generators.length === 0) {
        writeLine('term-cmd', '  ' + toolName + ' --help');
        return;
      }
      info.generators.forEach((gen, i) => {
        writeLine('term-gen-label', '  [' + (i+1) + '] ' + gen.label);
        writeLine('term-gen-cmd', '      $ ' + gen.cmd);
      });
      writeLine('', '');
      writeLine('term-welcome', '  Click any template in the 📋 panel to auto-fill.');
    } catch (err) {
      writeLine('term-error', '  Error: ' + (err.message || ''));
    }
  }

  // ===== GENERATORS PANEL =====
  async function loadGenerators() {
    try {
      const r = await Auth.api('/api/terminal/tools');
      toolGeneratorsCache = await r.json();
      renderGenerators();
      updatePrompt();
    } catch (_) {}
  }

  function renderGenerators(filter) {
    const list = $('#gen-list');
    if (!toolGeneratorsCache) return;
    list.innerHTML = '';
    const names = Object.keys(toolGeneratorsCache.tools).sort();
    names.forEach(name => {
      const info = toolGeneratorsCache.tools[name];
      if (filter && !name.includes(filter.toLowerCase())) return;

      const group = document.createElement('div');
      group.className = 'gen-group';

      const header = document.createElement('div');
      header.className = 'gen-group-header';
      header.textContent = name;
      header.addEventListener('click', () => {
        group.classList.toggle('gen-group-open');
      });
      group.appendChild(header);

      if (info.generators) {
        info.generators.forEach(gen => {
          const item = document.createElement('div');
          item.className = 'gen-item';
          item.innerHTML = '<span class="gen-item-label">' + gen.label + '</span>' +
            '<span class="gen-item-cmd">' + escapeHtml(gen.cmd) + '</span>';
          item.addEventListener('click', () => {
            inputEl().value = gen.cmd;
            inputEl().focus();
            if (gen.cmd.includes('{')) {
              const start = gen.cmd.indexOf('{');
              inputEl().setSelectionRange(start, start + 1);
            }
          });
          group.appendChild(item);
        });
      }
      list.appendChild(group);
    });
  }

  function filterGenerators() {
    renderGenerators($('#gen-search').value.trim());
  }

  function toggleGenerators() {
    const panel = $('#term-generators');
    panel.classList.toggle('hidden');
    if (!panel.classList.contains('hidden')) {
      renderGenerators();
      $('#gen-search').focus();
    }
  }

  // ===== TAB COMPLETION =====
  async function tabComplete() {
    const input = inputEl();
    const val = input.value.trim();
    if (!val) return;
    if (!toolGeneratorsCache) {
      try {
        const r = await Auth.api('/api/terminal/tools');
        toolGeneratorsCache = await r.json();
      } catch (_) { return; }
    }
    const toolNames = Object.keys(toolGeneratorsCache.tools);
    const matches = toolNames.filter(t => t.startsWith(val));
    if (matches.length === 1) {
      input.value = matches[0] + ' ';
    } else if (matches.length > 1) {
      writeLine('term-welcome', '  ' + matches.join('  '));
    }
  }

  return { init, openTerminal, runCommand };
})();

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => Term.init(), 500);
});
window.Term = Term;