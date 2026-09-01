const vscode = require('vscode');
const path = require('path');

// Get the current stack frame id (needed for 'watch'/'hover' evaluations).
async function getFrameId(session) {
  // Newer VS Code API: the focused stack item.
  const item = vscode.debug.activeStackItem;
  if (item && typeof item.frameId === 'number') {
    return item.frameId;
  }
  // Fallback: ask the debug adapter directly.
  try {
    let tid = item && typeof item.threadId === 'number' ? item.threadId : undefined;
    if (tid === undefined) {
      const threads = await session.customRequest('threads');
      tid = threads && threads.threads && threads.threads[0] && threads.threads[0].id;
    }
    if (tid === undefined) return undefined;
    const st = await session.customRequest('stackTrace', {
      threadId: tid, startFrame: 0, levels: 1
    });
    return st && st.stackFrames && st.stackFrames[0] && st.stackFrames[0].id;
  } catch (e) {
    return undefined;
  }
}

function activate(context) {
  const cmd = vscode.commands.registerCommand('runPy', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('runPy: no active editor');
      return;
    }
    // Selection if present, otherwise the whole file
    let text;
    if (editor.selection.isEmpty) {
      text = editor.document.getText();
    } else {
      text = editor.document.getText(editor.selection);
    }
    if (!text || text.trim() === '') {
      vscode.window.showWarningMessage('runPy: nothing to run');
      return;
    }
    const session = vscode.debug.activeDebugSession;
    if (!session) {
      vscode.window.showWarningMessage('runPy: no active debug session');
      return;
    }

    // --- added: silent preamble, run once before the visible lines ---
    const path0 = path.dirname(editor.document.uri.fsPath).replace(/\\/g, '/'); // NO DELETE
    const path1 = __dirname.replace(/\\/g, '/'); // NO DELETE
    
    //const preamble = `-exec python import sys; [sys.path.insert(0, p) for p in ["${path1}", "${path0}"] if p not in sys.path]; import importlib, mem; importlib.reload(mem); from mem import *;`;  
    const preamble = `-exec python import sys; sys.path[:0]=["${path0}","${path1}"]; import importlib, mem; importlib.reload(mem); from mem import *;`;
    
    const frameId = await getFrameId(session);
    try {
      await session.customRequest('evaluate', {
        expression: preamble,
        context: 'repl',
        frameId: frameId
      });
    } catch (e) {
      vscode.window.showErrorMessage('runPy preamble failed: ' + e.message);
      return;
    }
    // --- end added ---

    // --- added: distinguish file type (Python vs C++) ---
    const langId = editor.document.languageId; // e.g. 'python', 'cpp', 'c'
    const ext = path.extname(editor.document.uri.fsPath).toLowerCase(); // e.g. '.py', '.cpp'

    const isPython = langId === 'python' || ext === '.py';
    
    const CPP_LANGS = new Set(['c', 'cpp', 'cuda-cpp', 'cuda']);
    const CPP_EXTS = new Set([
      '.c', '.h',
      '.cpp', '.cc', '.cxx', '.c++', '.hpp', '.hh', '.hxx', '.h++',
      '.cu', '.cuh',
      '.inl', '.ipp', '.tpp',
    ]);    
    const isCpp = CPP_LANGS.has(langId) || CPP_EXTS.has(ext.toLowerCase());

    let strCommand = null; // FIX: was `None` (Python) and missing declaration; JS uses `null` + `let`

    if (isCpp) {
      // FIX: was Python f-string syntax; JS uses backtick template literals instead
      strCommand = `print('${text} =', cpu('${text}'))`;
    } else {
      // Default / Python branch: join selected lines, keep left indentation, trim trailing whitespace
      const lines = text
        .split(/\r?\n/)
        .map(line => line.replace(/\s+$/, ''));  // trim right only — keeps indentation
      strCommand = lines.join(' \n');
    }

    const payload = JSON.stringify(strCommand);
    const expr = `-exec python exec(${payload})`;
    try {
      await session.customRequest('evaluate', {
        expression: expr,
        context: 'repl',
        frameId: frameId
      });
    } catch (e) {
      vscode.window.showErrorMessage('runPy failed: ' + e.message);
      return;
    }
  });
  context.subscriptions.push(cmd);
}

function deactivate() {}
module.exports = { activate, deactivate };
