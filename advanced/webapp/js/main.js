// RISC-V Emulator - Main Application Logic
// Handles Pyodide initialization, execution loop, and coordination

let pyodide = null;
let emulatorTerminal = null;
let fileLoader = null;
let controlsManager = null;
let isRunning = false;
let instructionCount = 0;
let lastStatsUpdate = 0;
let lastInstructionCount = 0;  // Track instruction count at last stats update
let statsUpdateInterval = 500; // ms

// Status display
function updateStatus(message, isError = false) {
    const statusElement = document.getElementById('status-text');
    statusElement.textContent = message;
    statusElement.parentElement.className = isError ? 'status error' : 'status';
}

// Initialize Pyodide and set up Python environment
async function initializePyodide() {
    try {
        updateStatus('Loading Pyodide...');

        // Load Pyodide from CDN
        pyodide = await loadPyodide({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/'
        });

        updateStatus('Loading Python packages...');

        // Load pyelftools package
        await pyodide.loadPackage('micropip');
        await pyodide.runPythonAsync(`
            import micropip
            await micropip.install('pyelftools')
        `);

        updateStatus('Setting up Python import paths...');

        // Add directories to Python path
        await pyodide.runPythonAsync(`
            import sys
            sys.path.insert(0, '/home/pyodide')
            sys.path.insert(0, '/home/pyodide/py')
        `);

        updateStatus('Loading core emulator modules...');

        // Create directory structure in Pyodide filesystem
        try {
            pyodide.FS.mkdir('/home/pyodide/py');
        } catch (e) {
            // Directory might already exist, that's okay
        }

        // Add cache-busting timestamp to prevent browser caching of Python modules
        const cacheBust = Date.now();

        // Fetch core emulator modules from py directory
        const coreModules = ['cpu.py', 'ram.py', 'machine.py', 'rvc.py'];

        for (const moduleName of coreModules) {
            try {
                const response = await fetch(`py/${moduleName}?v=${cacheBust}`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch ${moduleName}: ${response.statusText}`);
                }
                const code = await response.text();
                pyodide.FS.writeFile(`/home/pyodide/${moduleName}`, code);
                console.log(`Loaded core module: ${moduleName}`);
            } catch (error) {
                console.error(`Error loading core module ${moduleName}:`, error);
                throw error;
            }
        }

        updateStatus('Loading browser-specific Python modules...');

        // Fetch and load browser-specific Python modules
        const pythonModules = ['browser_logger.py', 'browser_syscalls.py', 'browser_peripherals.py', 'browser_entry.py'];

        for (const moduleName of pythonModules) {
            try {
                const response = await fetch(`py/${moduleName}?v=${cacheBust}`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch ${moduleName}: ${response.statusText}`);
                }
                const code = await response.text();

                // Write to Pyodide filesystem
                pyodide.FS.writeFile(`/home/pyodide/py/${moduleName}`, code);
                console.log(`Loaded ${moduleName}`);
            } catch (error) {
                console.error(`Error loading ${moduleName}:`, error);
                throw error;
            }
        }

        updateStatus('Importing Python modules...');

        // Import browser_entry module
        await pyodide.runPythonAsync(`
            import browser_entry
            print("browser_entry module imported successfully")
        `);

        updateStatus('Emulator ready!');

        // Enable UI controls
        document.getElementById('btn-reset').disabled = false;

        return true;

    } catch (error) {
        console.error('Failed to initialize Pyodide:', error);
        updateStatus(`Initialization failed: ${error.message}`, true);
        return false;
    }
}

// Execution loop - runs chunks of instructions
async function runEmulationLoop() {
    if (!isRunning) return;

    try {
        // Run a chunk of instructions (10000 instructions per frame)
        const result = await pyodide.runPythonAsync('browser_entry.run_chunk(10000)');

        // Update instruction count
        const count = await pyodide.runPythonAsync('browser_entry.get_instruction_count()');
        instructionCount = count;

        // Update stats periodically
        const now = Date.now();
        if (now - lastStatsUpdate > statsUpdateInterval) {
            updatePerformanceStats();
            // lastStatsUpdate is updated inside updatePerformanceStats()
        }

        // Continue if emulator is still running
        if (result) {
            // Use setTimeout instead of requestAnimationFrame to allow input processing
            // This gives the browser time to process keyboard events
            setTimeout(() => requestAnimationFrame(runEmulationLoop), 0);
        } else {
            // Execution stopped (program exited or error)
            await stopEmulation();
            const exitInfo = await pyodide.runPythonAsync('browser_entry.get_exit_info()');
            updateStatus(`Execution stopped: ${exitInfo}`);

            // After exit/error, next run should restart from beginning
            document.getElementById('btn-run').textContent = 'Run';
        }

    } catch (error) {
        console.error('Execution error:', error);
        updateStatus(`Error: ${error.message}`, true);
        await stopEmulation();
    }
}

// Start emulation
async function startEmulation() {
    if (isRunning) return;

    try {
        updateStatus('Starting emulation...');

        // Start execution
        await pyodide.runPythonAsync('browser_entry.start()');

        isRunning = true;
        instructionCount = 0;
        lastInstructionCount = 0;
        lastStatsUpdate = Date.now();

        // Update UI
        const runButton = document.getElementById('btn-run');
        runButton.disabled = true;
        // After first run, button becomes "Resume" (will resume from stop, not restart)
        runButton.textContent = 'Resume';

        document.getElementById('btn-stop').disabled = false;
        updateStatus('Running...');

        // Start execution loop
        requestAnimationFrame(runEmulationLoop);

    } catch (error) {
        console.error('Failed to start emulation:', error);
        updateStatus(`Start failed: ${error.message}`, true);
    }
}

// Stop emulation
async function stopEmulation() {
    if (!isRunning) return;

    isRunning = false;

    // Call Python to log stop message
    try {
        await pyodide.runPythonAsync('browser_entry.stop()');
    } catch (error) {
        console.error('Error stopping emulation:', error);
    }

    // Update UI
    document.getElementById('btn-run').disabled = false;
    document.getElementById('btn-stop').disabled = true;

    updateStatus('Stopped');
    updatePerformanceStats();
}

// Reset emulator
async function resetEmulation() {
    await stopEmulation();

    try {
        updateStatus('Resetting emulator...');

        // Ensure I/O callbacks are available for reinit
        window.js_write_callback = emulatorTerminal.write.bind(emulatorTerminal);
        window.js_read_callback = emulatorTerminal.read.bind(emulatorTerminal);

        // Get current options
        const options = controlsManager.getOptions();

        // Update raw terminal mode
        emulatorTerminal.setRawMode(options.raw_tty);

        // Pass updated options to Python
        pyodide.globals.set('js_options', options);

        // Reset with current options (reinitializes and reloads)
        const result = await pyodide.runPythonAsync(`
            browser_entry.state.options = js_options.to_py()
            browser_entry.reset()
        `);

        if (result) {
            emulatorTerminal.clear();
            instructionCount = 0;
            lastInstructionCount = 0;
            updatePerformanceStats();
            updateStatus('Reset complete - options updated');

            // Reset complete - next run will start from beginning
            document.getElementById('btn-run').textContent = 'Run';

            // Update toggle availability based on file type
            const fileType = await pyodide.runPythonAsync('browser_entry.state.file_type');
            updateToggleAvailability(fileType);
        } else {
            updateStatus('Reset failed', true);
        }
    } catch (error) {
        console.error('Reset error:', error);
        updateStatus(`Reset failed: ${error.message}`, true);
    }
}

// Update performance statistics display
function updatePerformanceStats() {
    document.getElementById('stat-instructions').textContent = instructionCount.toLocaleString();

    // Calculate IPS (instructions per second)
    const now = Date.now();
    const timeDelta = (now - lastStatsUpdate) / 1000; // Convert to seconds
    const instructionDelta = instructionCount - lastInstructionCount;

    // Calculate IPS from the delta (instructions executed in this interval)
    const ips = timeDelta > 0 ? Math.round(instructionDelta / timeDelta) : 0;
    document.getElementById('stat-ips').textContent = ips.toLocaleString();

    // Update tracking variables for next calculation
    lastStatsUpdate = now;
    lastInstructionCount = instructionCount;
}

// File loaded callback
async function onFileLoaded(filename, filepath) {
    try {
        // Stop emulation if running
        if (isRunning) {
            await stopEmulation();
        }

        updateStatus(`Loading ${filename}...`);

        // Always set up I/O callbacks (they might be needed for reset/reinit)
        window.js_write_callback = emulatorTerminal.write.bind(emulatorTerminal);
        window.js_read_callback = emulatorTerminal.read.bind(emulatorTerminal);

        // Get current options
        const options = controlsManager.getOptions();

        // Set terminal raw mode based on option
        emulatorTerminal.setRawMode(options.raw_tty);

        // Check if emulator is initialized
        const isInitialized = await pyodide.runPythonAsync('browser_entry.state.initialized');

        if (!isInitialized) {
            updateStatus('Initializing emulator...');

            // Pass options to Python via globals (properly converts JS objects to Python)
            pyodide.globals.set('js_options', options);

            await pyodide.runPythonAsync(`
                import browser_entry
                browser_entry.initialize(js_options.to_py())
            `);
        }

        // Clear terminal for new file
        emulatorTerminal.clear();

        // Pass current options to Python for reinitialization
        pyodide.globals.set('js_options', options);

        // Call Python to load the file (with current options)
        const result = await pyodide.runPythonAsync(`
            browser_entry.load_file('${filepath}', js_options.to_py())
        `);

        if (result) {
            updateStatus(`${filename} loaded successfully`);
            const runButton = document.getElementById('btn-run');
            runButton.disabled = false;
            runButton.textContent = 'Run';  // New file loaded - will start from beginning

            // Get file type and disable symbol-dependent toggles for binary files
            const fileType = await pyodide.runPythonAsync('browser_entry.state.file_type');
            updateToggleAvailability(fileType);
        } else {
            updateStatus(`Failed to load ${filename}`, true);
            // Disable run button - no valid file loaded
            document.getElementById('btn-run').disabled = true;
        }

    } catch (error) {
        console.error('File load error:', error);
        updateStatus(`Error loading ${filename}: ${error.message}`, true);
        // Disable run button - file load failed
        document.getElementById('btn-run').disabled = true;
    }
}

// Update toggle availability based on file type
function updateToggleAvailability(fileType) {
    // Toggles that require ELF symbols/metadata
    const elfOnlyToggles = [
        { id: 'opt-trace-functions', reason: 'requires ELF symbols' },
        { id: 'opt-check-text', reason: 'requires ELF section metadata' }
    ];

    if (fileType === 'bin') {
        // Binary files don't have ELF metadata - disable and uncheck ELF-only features
        elfOnlyToggles.forEach(({ id, reason }) => {
            const checkbox = document.getElementById(id);
            const label = checkbox.parentElement;

            checkbox.disabled = true;
            checkbox.checked = false;
            label.style.opacity = '0.5';
            label.title = `Not available for binary files (${reason})`;
        });
    } else if (fileType === 'elf') {
        // ELF files have metadata - enable all features
        elfOnlyToggles.forEach(({ id }) => {
            const checkbox = document.getElementById(id);
            const label = checkbox.parentElement;

            checkbox.disabled = false;
            label.style.opacity = '1';
            label.title = '';
        });
    }
}

// Update options dynamically (tracing, checking, etc.)
async function updateOptions(options) {
    if (!pyodide) return;

    try {
        // Check if emulator is initialized
        const isInitialized = await pyodide.runPythonAsync('browser_entry.state.initialized');
        if (!isInitialized) return;

        // Pass options to Python
        pyodide.globals.set('js_options', options);

        // Update options in Python
        await pyodide.runPythonAsync(`
            browser_entry.update_options(js_options.to_py())
        `);
    } catch (error) {
        console.error('Failed to update options:', error);
    }
}

// Initialize application
async function initializeApp() {
    // Create terminal
    emulatorTerminal = new EmulatorTerminal('terminal');

    // Expose terminal globally so Python can access it
    window.emulatorTerminal = emulatorTerminal;

    // Create controls manager
    controlsManager = new ControlsManager();

    // Set up callback for option changes (tracing and checking)
    controlsManager.onOptionsChange = updateOptions;

    // Wire up buttons
    document.getElementById('btn-run').addEventListener('click', startEmulation);
    document.getElementById('btn-stop').addEventListener('click', stopEmulation);
    document.getElementById('btn-reset').addEventListener('click', resetEmulation);

    // Initialize Pyodide first
    const success = await initializePyodide();

    if (success) {
        // Create file loader AFTER pyodide is initialized
        fileLoader = new FileLoader('file-input', pyodide, onFileLoaded);

        // Enable file input now that Pyodide is ready
        document.getElementById('file-input').disabled = false;

        console.log('Application initialized successfully');
    }
    // Note: If initialization fails, file input stays disabled (grayed out)
}

// Start when page loads
window.addEventListener('DOMContentLoaded', initializeApp);
