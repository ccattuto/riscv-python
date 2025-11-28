// RISC-V Emulator - Controls Manager
// Handles UI controls and option collection

class ControlsManager {
    constructor() {
        // Cache element references
        this.elements = {
            // Tracing
            traceSyscalls: document.getElementById('opt-trace-syscalls'),
            traceTraps: document.getElementById('opt-trace-traps'),
            traceFunctions: document.getElementById('opt-trace-functions'),

            // Checking
            checkInv: document.getElementById('opt-check-inv'),
            checkRam: document.getElementById('opt-check-ram'),
            checkText: document.getElementById('opt-check-text'),

            // Features
            timer: document.getElementById('opt-timer'),
            rvc: document.getElementById('opt-rvc'),

            // Options
            rawTty: document.getElementById('opt-raw-tty'),
            regs: document.getElementById('opt-regs'),
            ramSize: document.getElementById('opt-ram-size')
        };

        // Callback for when options change
        this.onOptionsChange = null;

        // Set up listeners for dynamic options (tracing and checking)
        this.elements.traceSyscalls.addEventListener('change', () => this._handleOptionsChange());
        this.elements.traceTraps.addEventListener('change', () => this._handleOptionsChange());
        this.elements.traceFunctions.addEventListener('change', () => this._handleOptionsChange());
        this.elements.checkInv.addEventListener('change', () => this._handleOptionsChange());

        // Register field updates on blur (when user finishes editing)
        this.elements.regs.addEventListener('blur', () => this._handleOptionsChange());
    }

    _handleOptionsChange() {
        // Call callback if set
        if (this.onOptionsChange) {
            this.onOptionsChange(this.getOptions());
        }
    }

    // Collect all options from UI and return as object for Python
    getOptions() {
        const options = {
            // Tracing flags
            trace_syscalls: this.elements.traceSyscalls.checked,
            trace_traps: this.elements.traceTraps.checked,
            trace_functions: this.elements.traceFunctions.checked,

            // Checking flags
            check_inv: this.elements.checkInv.checked,
            check_ram: this.elements.checkRam.checked,
            check_text: this.elements.checkText.checked,

            // Features
            timer: this.elements.timer.checked,
            rvc: this.elements.rvc.checked,

            // Options
            raw_tty: this.elements.rawTty.checked,
            regs: this.parseRegisterList(this.elements.regs.value),
            ram_size: parseInt(this.elements.ramSize.value) * 1024  // Convert KB to bytes
        };

        return options;
    }

    // Parse comma-separated register list (e.g., "pc,sp,ra,a0" -> ["pc", "sp", "ra", "a0"])
    parseRegisterList(regString) {
        if (!regString || regString.trim() === '') {
            return [];
        }

        return regString.split(',').map(r => r.trim()).filter(r => r.length > 0);
    }

    // Reset all options to defaults
    resetToDefaults() {
        // Tracing - all off
        this.elements.traceSyscalls.checked = false;
        this.elements.traceTraps.checked = false;
        this.elements.traceFunctions.checked = false;

        // Checking - all off
        this.elements.checkInv.checked = false;
        this.elements.checkRam.checked = false;
        this.elements.checkText.checked = false;

        // Features - all off
        this.elements.timer.checked = false;
        this.elements.rvc.checked = false;

        // Options - defaults
        this.elements.regs.value = '';
        this.elements.ramSize.value = '1024';
    }

    // Get specific option value
    getOption(name) {
        const options = this.getOptions();
        return options[name];
    }

    // Set specific option value
    setOption(name, value) {
        switch (name) {
            case 'trace_syscalls':
                this.elements.traceSyscalls.checked = value;
                break;
            case 'trace_traps':
                this.elements.traceTraps.checked = value;
                break;
            case 'trace_functions':
                this.elements.traceFunctions.checked = value;
                break;
            case 'check_inv':
                this.elements.checkInv.checked = value;
                break;
            case 'check_ram':
                this.elements.checkRam.checked = value;
                break;
            case 'check_text':
                this.elements.checkText.checked = value;
                break;
            case 'timer':
                this.elements.timer.checked = value;
                break;
            case 'rvc':
                this.elements.rvc.checked = value;
                break;
            case 'regs':
                this.elements.regs.value = Array.isArray(value) ? value.join(',') : value;
                break;
            case 'ram_size':
                this.elements.ramSize.value = Math.floor(value / 1024);  // Convert bytes to KB
                break;
        }
    }
}
