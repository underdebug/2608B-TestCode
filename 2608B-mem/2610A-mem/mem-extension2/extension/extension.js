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

// Show the three most recent functions from caller to callee.
async function getStackFunction(session) {
  const item = vscode.debug.activeStackItem;
  let threadId = item && item.session === session ? item.threadId : undefined;
  if (threadId === undefined) {
    const response = await session.customRequest('threads');
    threadId = response.threads && response.threads[0] && response.threads[0].id;
  }
  if (threadId === undefined) {
    throw new Error('No debug thread is available. Pause the program first.');
  }
  const response = await session.customRequest('stackTrace', {
    threadId,
    startFrame: 0,
    levels: 4
  });
  return (response.stackFrames || []).slice(0, 4)//.reverse()
    .map(frame => frame.name.replace(/\(.*$/, '').trim())
    .join(' <- ');
}

// ------------------------------------------------------------
// 1. Disable Debug Console "Collapse Identical Lines"
// ------------------------------------------------------------
async function disableCollapseIdenticalLines() {
    const cfg = vscode.workspace.getConfiguration('debug');

    await cfg.update(
        'console.collapseIdenticalLines',
        false,
        vscode.ConfigurationTarget.Global
    );
}

// ------------------------------------------------------------
// 2. Set launch.json:
//    "internalConsoleOptions": "openOnSessionStart"
// ------------------------------------------------------------
async function openDebugConsoleOnStart() {
    const cfg = vscode.workspace.getConfiguration('launch');

    const configurations = cfg.get('configurations', []);

    let changed = false;

    for (const config of configurations) {
        if (config.internalConsoleOptions !== 'openOnSessionStart') {
            config.internalConsoleOptions = 'openOnSessionStart';
            changed = true;
        }
    }

    if (changed) {
        await cfg.update(
            'configurations',
            configurations,
            vscode.ConfigurationTarget.Workspace
        );
    }
}

async function activate(context) {
  //vscode.commands.executeCommand('workbench.panel.repl.view.focus');
  //~/.config/Code/User/settings.json
  //"debug.internalConsoleOptions": "openOnSessionStart"
  //.vscode/launch.json
  //"internalConsoleOptions": "openOnSessionStart"
  await disableCollapseIdenticalLines();
  await openDebugConsoleOnStart();

  const initializedSessions = new WeakSet();
 
  const cmd = vscode.commands.registerCommand('mem', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      //vscode.window.showWarningMessage('mem: no active editor');
      return;
    }

    const langId = editor.document.languageId;
    const ext = path.extname(editor.document.uri.fsPath).toLowerCase();
    const isPythonFile = langId === 'python' || ext === '.py';

    const session = vscode.debug.activeDebugSession;
    if (!session) {
      if (isPythonFile) {
        try {
          // Run the whole file when there is no selection. The Python
          // extension saves changes and uses the selected interpreter.
          if (editor.selection.isEmpty) {
            await vscode.commands.executeCommand('python.execInTerminal', editor.document.uri);
          } else {
            await vscode.commands.executeCommand('python.execSelectionInTerminal');
          }
        } catch (e) {
          vscode.window.showErrorMessage(
            'mem: Could not run Python. Enable the Microsoft Python extension and select an interpreter. ' + e.message
          );
        }
      } else {
        vscode.window.showWarningMessage('mem: Start a debug session to inspect C++ values.');
      }
      return;
    }

    
    // get isPythonProgram, isPythonFile
    let isPythonProgram = false;

    const session_type = (session.type || '').toLowerCase();
    if (['debugpy', 'python', 'pythonexperimental'].includes(session_type)) {
        isPythonProgram = true;
    }

    // get filePath, projectPath, extensionPath
    const filePath = path.dirname(editor.document.uri.fsPath).replace(/\\/g, '/');

    let projectPath = filePath
    const folder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
    if (folder) {
        projectPath = folder.uri.fsPath.replace(/\\/g, '/');
    }

    const extensionPath = __dirname.replace(/\\/g, '/');
    

    // get frameId
    const frameId = await getFrameId(session);
    let expression = null;

    if (!isPythonProgram) {
      if(!isPythonFile){ // c++ program, c++ code  
        if (!initializedSessions.has(session)) {
          // Mark before awaiting to prevent duplicate initialization.
          initializedSessions.add(session);
          expression = `-exec python import sys; sys.path[:0]=["${projectPath}/mem","${extensionPath}"]; import importlib, mem; importlib.reload(mem); from mem import *;`;
       
          try {
            await session.customRequest('evaluate', {
              expression: expression,
              context: 'repl',
              frameId: frameId
            });
          } 
          catch (e) {
            // Allow initialization to be retried after a failure.
            initializedSessions.delete(session);
            //vscode.window.showErrorMessage('mem expression failed: ' + e.message);
            return;
          }
        }
        

        const line = editor.selection.active.line + 1;
        let stack;
        try {
            stack = await getStackFunction(session);
            vscode.debug.activeDebugConsole.appendLine(`${line} ${stack}`);
        } catch {}

        
        let text;
        if (editor.selection.isEmpty) {
          const pos = editor.selection.active;               
          const range = editor.document.getWordRangeAtPosition(pos);
          if (!range){
            //vscode.window.showErrorMessage('editor.document.getWordRangeAtPosition failed');
            return
          }                                    
          
          text = editor.document.getText(range); // get cursor text
        } 
        else {
          text = editor.document.getText(editor.selection); // get selection
        }        

        expression = `${text} = mem('${text}'); print(${text}, '<= ${text}', list(${text}.shape) if hasattr(${text}, 'shape') and ${text}.shape else '', '${line}')`;
        expression = JSON.stringify(expression);
        
        const expr = `-exec python exec(${expression})`;
        try {
          await session.customRequest('evaluate', {
            expression: expr,
            context: 'repl',
            frameId: frameId
          });
          
          //vscode.commands.executeCommand('workbench.panel.repl.view.focus');
        } catch (e) {
          //vscode.window.showErrorMessage('mem expr failed: ' + e.message);
          return;
        }
      }
      else{ // c++ program, python code 
        if (!initializedSessions.has(session)) {
          // Mark before awaiting to prevent duplicate initialization.
          initializedSessions.add(session);
          expression = `-exec python import sys; sys.path[:0]=["${projectPath}/mem","${extensionPath}"]; import importlib, mem; importlib.reload(mem); from mem import *;`;
       
          try {
            await session.customRequest('evaluate', {
              expression: expression,
              context: 'repl',
              frameId: frameId
            });
          } 
          catch (e) {
            // Allow initialization to be retried after a failure.
            initializedSessions.delete(session);
            //vscode.window.showErrorMessage('mem expression failed: ' + e.message);
            return;
          }
        }

        const line = editor.selection.active.line + 1;
        let stack;
        try {
            stack = await getStackFunction(session);
            vscode.debug.activeDebugConsole.appendLine(`${line} ${stack}`);
        } catch {}
        

        let text;
        if (editor.selection.isEmpty) {
          text = editor.document.getText(); // get full text
        } 
        else {
          text = editor.document.getText(editor.selection); // get selection
        }

        
        const lines = text.split(/\r?\n/).map(line => line.replace(/\s+$/, ''));  // trim right
        expression = lines.join(' \n');
        expression = JSON.stringify(expression);

        const expr = `-exec python exec(${expression})`;
        try {
          await session.customRequest('evaluate', {
            expression: expr,
            context: 'repl',
            frameId: frameId
          });
        } catch (e) {
          //vscode.window.showErrorMessage('mem expression failed: ' + e.message);
          return;
        } 
      }
    }
    else { // python program, python code
      if (isPythonFile) { // debug in python code
        const line = editor.selection.active.line + 1;
        let stack;
        try {
            stack = await getStackFunction(session);
            vscode.debug.activeDebugConsole.appendLine(`${line} ${stack}`);
        } catch {}

        if (editor.selection.isEmpty) {
          const pos = editor.selection.active;
          const range = editor.document.getWordRangeAtPosition(pos);
          if (range) {
            const text = editor.document.getText(range);
            expression = `print(${text}, '<= ${text}', list(${text}.shape) if hasattr(${text}, 'shape') and ${text}.shape else '', '${pos.line + 1}')`;
          } else { // cursor is not on a word -> run current line
            expression = editor.document.lineAt(pos.line).text;
          }
        } else { // run selected code
          expression = editor.document.getText(editor.selection);
        }

        try {
          await session.customRequest('evaluate', {
            expression: expression,
            context: 'repl',
            frameId: frameId
          });
        } catch (e) {
          //vscode.window.showErrorMessage('mem expression failed: ' + e.message);
          return;
        }
      }
    }
  });
  context.subscriptions.push(cmd);
}

function deactivate() {}
module.exports = { activate, deactivate };
