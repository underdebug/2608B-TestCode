
vsce package --allow-missing-repository --skip-license
code --uninstall-extension local.runPy
code --install-extension runPy-0.0.1.vsix


: '
bash: ./install.sh: Permission denied
bash install.sh                    <=

~/.vscode/extensions
/home/roots/.vscode/extensions/local.runpy-0.0.1

/home/roots/.config/Code/User/keybindings.json

    {
    	"key": "f7",
    	"command": "editor.debug.action.selectionToRepl",
    	"when": "editorHasSelection && inDebugMode"
    },
    {
        "key": "f8",
        "command": "f8run.comma",
        "when": "editorTextFocus && inDebugMode"
    }

Ctrl + Shift + P
Reload Window
'

: << 'COMMENT'

1) test
Extension Development Host


2) install

node --version
npm --version

sudo npm install -g @vscode/vsce

cd f8comma
vsce package --allow-missing-repository --skip-license


Ctrl + Shit + P
Extensions: Install from VSIX...

Or:
code --install-extension f8comma-0.0.1.vsix

COMMENT


