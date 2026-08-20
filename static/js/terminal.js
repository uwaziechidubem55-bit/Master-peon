// ===== TERMINAL ENGINE =====
const Term = (() => {
  const outputEl = () => $('#terminal-output');
  const inputEl = () => $('#terminal-input');

  let commandHistory = [];
  let historyIndex = -1;
  let toolGeneratorsCache = null;
  let terminalOpen = false;

  function init() {
    // Load tool generators on startup
    loadGenerators();

    // Terminal input handling
    inputEl().addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        runCommand();
      }
      // History navigation
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
      // Ctrl+Space to toggle generators
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

    // Clear button
    $('#terminal-clear').addEventListener('click', () => {
      outputEl().innerHTML = '';
      writeLine('', 'term-welcome', 'Terminal cleared. Type help for commands.');
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

    // Keyboard shortcut Ctrl+`
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

    // Write initial welcome
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
    writeLine('', 'term-banner', '╔══════════════════════════════════════════╗');
    writeLine('', 'term-banner', '║        MASTER PEON TERMINAL v1.0          ║');
    writeLine('', 'term-banner', '║     AI-Assisted Penetration Testing       ║');
    writeLine('', 'term-banner', '╚══════════════════════════════════════════╝');
    writeLine('', '', '');
    writeLine('', 'term-welcome', '  Type "help" for available commands');
    writeLine('', 'term-welcome', '  Type "tools" to see your available tools');
    writeLine('', 'term-welcome', '  Type "generate <tool>" for command templates');
    writeLine('', 'term-welcome', '  Press Ctrl+Space to browse tool generators');
    writeLine('', 'term-welcome', '  Press Up/Down for command history');
    writeLine('', 'term-welcome', '  Press Tab for command completion');
    writeLine('', '', '');
    updatePrompt();
  }

  function writeLine(type, cls, text) {
    const line = document.createElement('div');
    line.className = 'term-line' + (cls ? ' ' + cls : '');
    if (type === 'input') {
      line.innerHTML = '<span class="term-prompt-inline">peon@kali:~$</span> ' + escapeHtml(text);
    } else {
      line.textContent = text;
    }
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

    // Show input line
    writeLine('input', '', cmd);

    // Built-in commands
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
      commandHistory.forEach((c, i) => writeLine('', '', (i+1) + '  ' + c));
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

    // Send to backend
    writeLine('', 'term-info', '⏳ Running...');
    try {
      const r = await Auth.api('/api/terminal/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
      });
      const data = await r.json();

      // Remove the "Running..." line
      const lines = outputEl().querySelectorAll('.term-line');
      for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].textContent === '⏳ Running...') {
          lines[i].remove();
          break;
        }
      }

      if (data.output) {
        writeOutput(data.output, 'term-output');
      }
      if (data.exit_code && data.exit_code !== 0) {
        writeLine('', 'term-error', '\n[!] Exit code: ' + data.exit_code);
      }
    } catch (err) {
      // Remove the "Running..." line
      const lines = outputEl().querySelectorAll('.term-line');
      for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].textContent === '⏳ Running...') {
          lines[i].remove();
          break;
        }
      }
      
      if (err.message && err.message.includes('403')) {
        writeLine('', 'term-error', '[!] Access denied: Tool not available on your tier.');
        writeLine('', 'term-welcome', '    Upgrade your plan to unlock more tools.');
      } else if (err.message && err.message.includes('429')) {
        writeLine('', 'term-error', '[!] Daily tool-call limit reached for your tier.');
      } else if (err.message && err.message.includes('400')) {
        // Try to get the detail from the response
        writeLine('', 'term-error', '[!] ' + (err.detail || 'Invalid command'));
      } else {
        writeLine('', 'term-error', '[!] Error: ' + (err.message || 'Request failed'));
      }
    }
    outputEl().scrollTop = outputEl().scrollHeight;
  }

  // ===== SHOW HELP =====
  async function showHelp() {
    writeLine('', 'term-title', '═══ MASTER PEON TERMINAL HELP ═══');
    writeLine('', '', '');
    writeLine('', 'term-section', 'Built-in Commands:');
    writeLine('', 'term-cmd', '  clear            Clear terminal screen');
    writeLine('', 'term-cmd', '  help             Show this help');
    writeLine('', 'term-cmd', '  history          Show command history');
    writeLine('', 'term-cmd', '  tools            List available security tools');
    writeLine('', 'term-cmd', '  generate <tool>  Show command templates for a tool');
    writeLine('', '', '');
    writeLine('', 'term-section', 'General Commands (all tiers):');
    writeLine('', 'term-cmd', '  ls, cat, head, tail, echo, pwd, whoami');
    writeLine('', 'term-cmd', '  id, date, df, free, uptime, uname, hostname');
    writeLine('', 'term-cmd', '  grep, find, sort, wc, which, file, stat');
    writeLine('', '', '');
    writeLine('', 'term-section', 'Security Tools (tier-dependent):');
    writeLine('', 'term-cmd', '  Type "tools" to see your available tools');
    writeLine('', 'term-cmd', '  Type "generate <tool>" for command templates');
    writeLine('', '', '');
    writeLine('', 'term-section', 'Shortcuts:');
    writeLine('', 'term-cmd', '  Ctrl+`          Toggle terminal');
    writeLine('', 'term-cmd', '  Ctrl+Space      Browse tool command generators');
    writeLine('', 'term-cmd', '  Up/Down         Command history');
    writeLine('', 'term-cmd', '  Tab             Command completion');
    writeLine('', '', '');
    writeLine('', 'term-welcome', '  Pro tip: Click 📋 in terminal header for tool generators');
  }

  // ===== SHOW TOOLS =====
  async function showTools() {
    writeLine('', 'term-title', '═══ YOUR AVAILABLE TOOLS ═══');
    writeLine('', '', '');
    try {
      const r = await Auth.api('/api/terminal/tools');
      const data = await r.json();
      writeLine('', 'term-welcome', '  Tier: ' + data.tier.toUpperCase());
      writeLine('', '', '');
      const names = Object.keys(data.tools);
      if (names.length === 0) {
        writeLine('', 'term-error', '  No tools available on your current tier.');
      } else {
        // Show in columns
        let line = '';
        names.forEach((name, i) => {
          line += name.padEnd(16);
          if ((i + 1) % 4 === 0) {
            writeLine('', 'term-tool', '  ' + line);
            line = '';
          }
        });
        if (line) writeLine('', 'term-tool', '  ' + line);
      }
      writeLine('', '', '');
      writeLine('', 'term-welcome', '  Use "generate <toolname>" for command templates.');
    } catch (err) {
      writeLine('', 'term-error', '  Failed to load tools: ' + (err.message || ''));
    }
  }

  // ===== SHOW TOOL GENERATORS =====
  async function showToolGenerators(toolName) {
    try {
      const r = await Auth.api('/api/terminal/tools');
      const data = await r.json();
      const info = data.tools[toolName];
      if (!info) {
        writeLine('', 'term-error', '  Tool "' + toolName + '" not found or not available on your tier.');
        return;
      }
      writeLine('', 'term-title', '═══ ' + toolName.toUpperCase() + ' — Command Generators ═══');
      writeLine('', '', '');
      if (!info.generators || info.generators.length === 0) {
        writeLine('', 'term-welcome', '  No predefined generators. Use tool directly:');
        writeLine('', 'term-cmd', '  ' + toolName + ' --help');
        return;
      }
      info.generators.forEach((gen, i) => {
        writeLine('', 'term-gen-label', '  [' + (i+1) + '] ' + gen.label);
        writeLine('', 'term-gen-cmd', '      ' + gen.cmd);
      });
      writeLine('', '', '');
      writeLine('', 'term-welcome', '  Click a generator in the 📋 panel to auto-fill.');
    } catch (err) {
      writeLine('', 'term-error', '  Error: ' + (err.message || ''));
    }
  }

  // ===== LOAD GENERATORS =====
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
            // Insert {placeholders} for user to fill
            if (gen.cmd.includes('{')) {
              // Move cursor to first placeholder
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
    const val = $('#gen-search').value.trim();
    renderGenerators(val);
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

    // Try to get tools from cache or API
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
      // Show matches
      writeLine('', 'term-welcome', matches.join('  '));
    }
  }

  // ===== PUBLIC API =====
  return {
    init,
    openTerminal,
    runCommand,
  };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Wait a moment for auth to load
  setTimeout(() => Term.init(), 500);
});

// Expose so app.js can trigger
window.Term = Term;