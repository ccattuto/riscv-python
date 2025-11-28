// RISC-V Emulator - Terminal Integration
// Handles xterm.js terminal with raw TTY support (character-at-a-time input)

class EmulatorTerminal {
    constructor(containerId) {
        this.terminal = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
                background: '#1e1e1e',
                foreground: '#d4d4d4',
                cursor: '#d4d4d4',
                black: '#000000',
                red: '#cd3131',
                green: '#0dbc79',
                yellow: '#e5e510',
                blue: '#2472c8',
                magenta: '#bc3fbc',
                cyan: '#11a8cd',
                white: '#e5e5e5',
                brightBlack: '#666666',
                brightRed: '#f14c4c',
                brightGreen: '#23d18b',
                brightYellow: '#f5f543',
                brightBlue: '#3b8eea',
                brightMagenta: '#d670d6',
                brightCyan: '#29b8db',
                brightWhite: '#ffffff'
            },
            rows: 30,
            cols: 100
        });

        // Fit addon for responsive sizing
        this.fitAddon = new FitAddon.FitAddon();
        this.terminal.loadAddon(this.fitAddon);

        // Open terminal in container
        const container = document.getElementById(containerId);
        this.terminal.open(container);
        this.fitAddon.fit();

        // Input buffer for character-at-a-time reads
        this.inputBuffer = [];

        // Pending read requests
        this.pendingReads = [];

        // Raw mode flag (no auto-echo when true)
        this.rawMode = false;

        // Set up input handling
        this.setupInputHandling();

        // Handle window resize
        window.addEventListener('resize', () => {
            this.fitAddon.fit();
        });
    }

    // Set raw mode (true = no auto-echo, false = auto-echo)
    setRawMode(enabled) {
        this.rawMode = enabled;
    }

    setupInputHandling() {
        // Capture all key inputs
        this.terminal.onData((data) => {
            // Handle special keys
            if (data === '\x03') {
                // Ctrl-C
                this.handleCtrlC();
                return;
            }

            // Add data to input buffer
            for (let i = 0; i < data.length; i++) {
                this.inputBuffer.push(data.charCodeAt(i));
            }

            // Echo the input only if NOT in raw mode
            // In raw mode, the program itself handles echoing
            if (!this.rawMode) {
                this.terminal.write(data);
            }

            // Process any pending reads
            this.processPendingReads();
        });
    }

    handleCtrlC() {
        this.terminal.write('^C\r\n');

        // TODO: Signal to stop emulation
        // For now, just log it
        console.log('Ctrl-C pressed');

        // Trigger stop button click
        const stopButton = document.getElementById('btn-stop');
        if (stopButton && !stopButton.disabled) {
            stopButton.click();
        }
    }

    // Write output to terminal (called from Python syscall handler)
    write(data) {
        let text;

        if (typeof data === 'string') {
            text = data;
        } else if (data instanceof Uint8Array) {
            // Convert bytes to string
            text = new TextDecoder().decode(data);
        } else if (Array.isArray(data)) {
            // Array of byte values
            const uint8Array = new Uint8Array(data);
            text = new TextDecoder().decode(uint8Array);
        } else if (data && typeof data === 'object' && 'buffer' in data) {
            // Pyodide memoryview-like object
            const uint8Array = new Uint8Array(data.buffer || data);
            text = new TextDecoder().decode(uint8Array);
        } else {
            console.error('[Terminal] Unexpected data type for terminal.write:', typeof data, data);
            return;
        }

        // Convert Unix newlines (\n) to terminal newlines (\r\n)
        text = text.replace(/\n/g, '\r\n');

        this.terminal.write(text);
    }

    // Read input from terminal (called from Python syscall handler)
    // Returns a Promise that resolves with Uint8Array of requested bytes
    async read(count) {
        return new Promise((resolve) => {
            // If we have enough data in buffer, return immediately
            if (this.inputBuffer.length >= count) {
                const data = this.inputBuffer.splice(0, count);
                resolve(new Uint8Array(data));
            } else {
                // Queue this read request
                this.pendingReads.push({ count, resolve });
            }
        });
    }

    // Process any pending read requests
    processPendingReads() {
        while (this.pendingReads.length > 0 && this.inputBuffer.length > 0) {
            const request = this.pendingReads[0];

            if (this.inputBuffer.length >= request.count) {
                // We have enough data
                const data = this.inputBuffer.splice(0, request.count);
                request.resolve(new Uint8Array(data));
                this.pendingReads.shift();
            } else {
                // Not enough data yet
                break;
            }
        }
    }

    // Clear terminal
    clear() {
        this.terminal.clear();
        this.inputBuffer = [];
        this.pendingReads = [];
    }

    // Write a line (convenience method)
    writeln(text) {
        this.terminal.writeln(text);
    }
}
