"""
Browser Entry Point - Main interface between JavaScript and Python emulator
Handles initialization, file loading, and chunked execution

State Management Architecture:
- initialize(): Creates CPU, RAM, Machine with specified options
- load_file(options): ALWAYS does full reinitialization with fresh UI options, then loads executable
- start(): Starts OR resumes execution
  - After load/reset/exit: restarts from entry point
  - After stop: resumes from current PC
- stop(): Pauses execution (preserves PC for resume)
- reset(): Full clean reset - reinitializes CPU/RAM/Machine and reloads current file with current options
- run_chunk(): Executes a batch of instructions

Key principles:
- Programs manage their own RAM/register initialization via start.S
- Loading any file (even same filename) always reinitializes for clean execution
- Stop/Run provides pause/resume capability
- Only Reset or program exit restarts from beginning
"""

from cpu import CPU
from ram import RAM, SafeRAM, RAM_MMIO, SafeRAM_MMIO
from machine import Machine, MachineError, ExecutionTerminated
from browser_syscalls import BrowserSyscallHandler
from browser_logger import BrowserLogger
import js

# Global emulator state
class EmulatorState:
    def __init__(self):
        self.cpu = None
        self.ram = None
        self.machine = None
        self.syscall_handler = None
        self.logger = None
        self.options = {}
        self.running = False
        self.instruction_count = 0
        self.exit_info = ""
        self.initialized = False
        self.file_loaded = False
        self.loaded_filepath = None  # Store path for reset/reload
        self.file_type = None  # 'elf' or 'bin'
        # Store initial state for reset (PC only - programs handle SP via start.S)
        self.initial_pc = 0
        self.initial_heap_end = 0
        # Track whether next start() should reset PC or resume from current PC
        self.should_reset_pc = True  # True = restart from beginning, False = resume

# Single global state instance
state = EmulatorState()

def initialize(options):
    """
    Initialize the emulator with given options.

    Args:
        options: Dict with keys:
            - trace_syscalls: bool
            - trace_traps: bool
            - trace_functions: bool
            - check_inv: bool
            - check_ram: bool
            - check_text: bool
            - timer: bool
            - rvc: bool
            - regs: list of register names to log
            - ram_size: int (bytes)
    """
    global state

    try:
        state.logger = BrowserLogger('emulator')
        state.logger.info('Initializing emulator...')

        # Store options
        state.options = options

        # Determine if we need MMIO
        timer_enabled = options.get('timer', False)
        use_mmio = timer_enabled  # In browser, only timer uses MMIO

        # Create RAM (choose implementation based on options)
        ram_size = options.get('ram_size', 1024 * 1024)  # default 1MB
        check_ram = options.get('check_ram', False)

        # Select RAM implementation (matching riscv-emu.py pattern)
        if not use_mmio and not check_ram:
            state.ram = RAM(ram_size, init='zero', logger=state.logger)
        elif use_mmio and not check_ram:
            state.ram = RAM_MMIO(ram_size, init='zero', logger=state.logger)
        elif not use_mmio and check_ram:
            state.ram = SafeRAM(ram_size, init='zero', logger=state.logger)
        else:
            state.ram = SafeRAM_MMIO(ram_size, init='zero', logger=state.logger)

        # Create CPU (needs ram as first argument)
        rvc = options.get('rvc', False)
        trace_traps = options.get('trace_traps', False)
        state.cpu = CPU(
            state.ram,
            rvc_enabled=rvc,
            logger=state.logger,
            trace_traps=trace_traps
        )

        # Create Machine (matching riscv-emu.py pattern)
        # Always pass logger so we can enable/disable tracing dynamically
        state.machine = Machine(
            state.cpu,
            state.ram,
            timer=timer_enabled,
            mmio=use_mmio,
            rvc=rvc,
            logger=state.logger,  # Always pass logger for dynamic tracing
            trace=options.get('trace_functions', False),
            regs=options.get('regs', []),
            check_inv=options.get('check_inv', False)
        )

        # Register timer peripheral if enabled
        if timer_enabled:
            try:
                from browser_peripherals import MMIOTimer
                timer_peripheral = MMIOTimer(state.cpu)
                state.ram.register_peripheral(timer_peripheral)
                state.machine.register_peripheral(timer_peripheral)
                state.logger.info('Timer peripheral registered')
            except ImportError:
                state.logger.warning('Timer requested but peripherals.py not available')

        # Create and register syscall handler (AFTER machine)
        write_callback = js.js_write_callback if hasattr(js, 'js_write_callback') else None
        read_callback = js.js_read_callback if hasattr(js, 'js_read_callback') else None

        state.syscall_handler = BrowserSyscallHandler(
            state.cpu,
            state.ram,
            state.machine,
            logger=state.logger,  # Always pass logger for dynamic tracing
            trace_syscalls=options.get('trace_syscalls', False),
            write_callback=write_callback,
            read_callback=read_callback
        )

        # Set syscall handler on CPU
        state.cpu.set_ecall_handler(state.syscall_handler.handle)

        state.initialized = True
        state.logger.info('Emulator initialized successfully')
        return True

    except Exception as e:
        if state.logger:
            state.logger.error(f'Initialization failed: {e}')
        raise

def load_file(filepath, options=None):
    """
    Load an ELF or binary file into emulated RAM.
    ALWAYS performs full reinitialization to ensure clean state (even for same filename).

    Args:
        filepath: Path to file in Pyodide virtual filesystem (e.g., '/tmp/program.elf')
        options: Fresh options from UI (if not provided, uses current state.options)

    Returns:
        bool: True if loaded successfully
    """
    global state

    if not state.initialized:
        if state.logger:
            state.logger.error('Emulator not initialized')
        else:
            print('ERROR: Emulator not initialized')
        return False

    # Always do full reinitialization when loading a file
    # (User may have recompiled same filename, or changed toggles)
    if state.file_loaded:
        state.logger.info(f'Loading file - performing full reinitialization...')

        # Use provided options (fresh from UI) or fall back to current state
        if options is None:
            options = state.options

        # Mark as uninitialized to force full reinit
        state.initialized = False
        state.file_loaded = False

        # Re-initialize with current options
        try:
            initialize(options)
        except Exception as e:
            state.logger.error(f'Reinitialization failed: {e}')
            return False

    try:
        state.logger.info(f'Loading {filepath}...')

        # Determine file type by extension
        if filepath.lower().endswith('.elf'):
            # Load ELF file
            load_symbols = state.options.get('trace_functions', False)
            check_text = state.options.get('check_text', False)
            state.machine.load_elf(filepath, load_symbols=load_symbols, check_text=check_text)
            state.file_type = 'elf'
            state.logger.info(f'ELF file loaded: entry=0x{state.cpu.pc:08X}')
            state.logger.info(f'Stack: top=0x{state.machine.stack_top:08X} bottom=0x{state.machine.stack_bottom:08X}' if state.machine.stack_top else 'Stack: not set')
            state.logger.info(f'Heap: start=0x{state.machine.heap_end:08X}' if state.machine.heap_end else 'Heap: not set')
            state.logger.info(f'Initial registers: PC=0x{state.cpu.pc:08X} SP=0x{state.cpu.registers[2]:08X}')

            # Validate that ELF memory layout fits within configured RAM size
            ram_size = state.ram.size
            required_size = 0
            if state.machine.stack_top:
                required_size = max(required_size, state.machine.stack_top)
            if state.machine.heap_end:
                required_size = max(required_size, state.machine.heap_end)

            if required_size > ram_size:
                state.logger.error(f'ELF requires {required_size // 1024}KB RAM but only {ram_size // 1024}KB configured')
                state.logger.error(f'Increase RAM size to at least {((required_size + 1023) // 1024)}KB and reload')
                return False

        elif filepath.lower().endswith('.bin'):
            # Load flat binary
            state.machine.load_flatbinary(filepath)
            state.file_type = 'bin'
            state.logger.info(f'Binary file loaded: entry=0x{state.cpu.pc:08X}')

        else:
            state.logger.error(f'Unknown file type: {filepath}')
            return False

        # Store initial state for reset
        state.initial_pc = state.cpu.pc
        state.initial_heap_end = state.machine.heap_end if state.machine.heap_end else 0

        # Store filepath for reset/reload
        state.loaded_filepath = filepath

        state.file_loaded = True
        state.instruction_count = 0

        # New file loaded - next start() should begin from entry point
        state.should_reset_pc = True

        return True

    except Exception as e:
        state.logger.error(f'File loading failed: {e}')
        return False

def start():
    """
    Start/resume emulation.
    - If should_reset_pc=True: restart from beginning (after load/reset/exit)
    - If should_reset_pc=False: resume from current PC (after stop)
    """
    global state

    if not state.initialized or not state.file_loaded:
        raise RuntimeError('Emulator not ready')

    # Only reset PC if this is a fresh start (after load/reset/exit)
    # Otherwise resume from current PC (after stop)
    if state.should_reset_pc:
        state.cpu.pc = state.initial_pc
        # Don't set next_pc - it will be set correctly by execute() based on instruction size
        state.machine.heap_end = state.initial_heap_end
        state.instruction_count = 0  # Reset instruction count for fresh start
        state.logger.info('Emulation started')
    else:
        state.logger.info('Emulation resumed')

    state.running = True
    state.exit_info = ""

    # After starting, clear the flag so stop/run will resume
    state.should_reset_pc = False

def stop():
    """Stop emulation - just controls execution, doesn't reset state"""
    global state
    state.running = False
    state.logger.info('Emulation stopped')

def reset():
    """
    Full clean reset - reinitializes emulator (CPU, RAM, Machine) and reloads current file.
    Applies current UI option changes (timer, RVC, check_ram, etc.)
    """
    global state

    if not state.file_loaded or not state.loaded_filepath:
        if state.logger:
            state.logger.warning('No file loaded, cannot reset')
        return False

    if state.logger:
        state.logger.info('Resetting emulator (full reinitialization with current options)...')

    # Store filepath and options before clearing state
    filepath = state.loaded_filepath
    options = state.options

    # Clear initialized flag to force full reinitialization
    state.initialized = False
    state.file_loaded = False

    # Re-initialize with current options (this will recreate CPU, RAM, Machine with new settings)
    try:
        # Import here to access js callbacks
        import js

        # Re-initialize
        initialize(options)

        # Reload the file
        return load_file(filepath)

    except Exception as e:
        if state.logger:
            state.logger.error(f'Reset failed: {e}')
        return False

def run_chunk(instruction_count=10000):
    """
    Execute a chunk of instructions.

    Args:
        instruction_count: Number of instructions to execute

    Returns:
        bool: True if should continue, False if execution stopped
    """
    global state

    if not state.running:
        return False

    # Create register formatter if needed
    regformatter = None
    if state.machine.regs:
        regformatter = state.machine.make_regformatter_lambda(','.join(state.machine.regs))

    try:
        # Execute instructions
        for _ in range(instruction_count):
            # Log registers if enabled (use cyan color for better distinction)
            if regformatter and state.logger:
                import js
                if state.logger.write_to_terminal and hasattr(js.window, 'emulatorTerminal'):
                    # Write register dump in cyan directly to terminal
                    reg_output = f'\033[36m[DEBUG] REGS: {regformatter(state.cpu)}\033[0m\r\n'
                    js.window.emulatorTerminal.terminal.write(reg_output)
                # Still log to console
                js.console.log(f'[{state.logger.name}] DEBUG: REGS: {regformatter(state.cpu)}')

            # Check for function tracing (before executing instruction)
            if state.machine.trace and (state.cpu.pc in state.machine.symbol_dict):
                func_name = state.machine.symbol_dict[state.cpu.pc]
                if state.logger:
                    state.logger.debug(f"FUNC {func_name}, PC={state.cpu.pc:08X}")

            # Check invariants if enabled
            if state.machine.check_inv:
                state.machine.check_invariants()

            # Fetch instruction (always load full word, execute() will handle RVC)
            inst = state.ram.load_word(state.cpu.pc)

            # Execute (dispatches to execute_32 or execute_16 based on inst type)
            state.cpu.execute(inst)

            # Update timer if enabled
            if state.options.get('timer', False):
                state.cpu.timer_update()

            # Update PC
            state.cpu.pc = state.cpu.next_pc

            state.instruction_count += 1

        # Still running
        return True

    except ExecutionTerminated as e:
        # Normal program exit - next run should restart from beginning
        state.exit_info = str(e)
        state.running = False
        state.should_reset_pc = True
        state.logger.info(f'Execution terminated: {e}')
        return False

    except MachineError as e:
        # Error during execution - next run should restart from beginning
        state.exit_info = f'Error: {e}'
        state.running = False
        state.should_reset_pc = True
        state.logger.error(f'Execution error: {e}')
        return False

    except Exception as e:
        # Unexpected error - next run should restart from beginning
        state.exit_info = f'Unexpected error: {e}'
        state.running = False
        state.should_reset_pc = True
        state.logger.error(f'Unexpected error: {e}')
        return False

def get_instruction_count():
    """Get total instruction count"""
    return state.instruction_count

def get_exit_info():
    """Get exit/error information"""
    return state.exit_info

def is_running():
    """Check if emulator is running"""
    return state.running

def update_options(options):
    """Update tracing/logging/checking options dynamically without reloading"""
    global state

    if not state.initialized:
        return False

    # Update stored options
    state.options = options

    # Update syscall handler trace flag
    if state.syscall_handler:
        state.syscall_handler.trace_syscalls = options.get('trace_syscalls', False)

    # Update CPU trace flag
    if state.cpu:
        state.cpu.trace_traps = options.get('trace_traps', False)

    # Update machine trace and checking flags
    if state.machine:
        state.machine.trace = options.get('trace_functions', False)
        state.machine.check_inv = options.get('check_inv', False)
        # Update register list if needed
        regs = options.get('regs', [])
        if regs != state.machine.regs:
            state.machine.regs = regs

    # Note: check_ram and check_text require specific RAM implementations
    # and cannot be toggled dynamically (require reload)

    if state.logger:
        state.logger.info('Options updated')

    return True
