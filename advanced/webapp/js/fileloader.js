// RISC-V Emulator - File Loader
// Handles loading ELF/bin files via FileAPI and writing to Pyodide virtual filesystem

class FileLoader {
    constructor(inputElementId, pyodideInstance, onLoadCallback) {
        this.inputElement = document.getElementById(inputElementId);
        this.pyodide = pyodideInstance;
        this.onLoadCallback = onLoadCallback;
        this.currentFile = null;

        // Set up file input handler
        this.inputElement.addEventListener('change', (event) => {
            this.handleFileSelect(event);
        });
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            // Validate file extension
            const filename = file.name.toLowerCase();
            if (!filename.endsWith('.elf') && !filename.endsWith('.bin')) {
                this.showFileInfo(`Invalid file type. Please select a .elf or .bin file.`, true);
                return;
            }

            this.showFileInfo(`Loading ${file.name} (${this.formatBytes(file.size)})...`);

            // Read file as ArrayBuffer
            const arrayBuffer = await this.readFileAsArrayBuffer(file);

            // Write to Pyodide virtual filesystem at /tmp/
            const filepath = `/tmp/${file.name}`;
            this.writeFileToPyodide(filepath, arrayBuffer);

            this.currentFile = {
                name: file.name,
                size: file.size,
                path: filepath
            };

            this.showFileInfo(`${file.name} (${this.formatBytes(file.size)}) loaded`);

            // Call the callback if provided
            if (this.onLoadCallback) {
                await this.onLoadCallback(file.name, filepath);
            }

        } catch (error) {
            console.error('File loading error:', error);
            this.showFileInfo(`Error loading file: ${error.message}`, true);
        }
    }

    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (event) => {
                resolve(event.target.result);
            };

            reader.onerror = (error) => {
                reject(error);
            };

            reader.readAsArrayBuffer(file);
        });
    }

    writeFileToPyodide(filepath, arrayBuffer) {
        // Ensure /tmp directory exists
        try {
            this.pyodide.FS.mkdir('/tmp');
        } catch (e) {
            // Directory might already exist
        }

        // Convert ArrayBuffer to Uint8Array
        const uint8Array = new Uint8Array(arrayBuffer);

        // Write file to Pyodide virtual filesystem
        this.pyodide.FS.writeFile(filepath, uint8Array);

        console.log(`Wrote ${uint8Array.length} bytes to ${filepath}`);
    }

    showFileInfo(message, isError = false) {
        const fileInfo = document.getElementById('file-info');
        if (fileInfo) {
            fileInfo.textContent = message;
            fileInfo.className = isError ? 'file-info error' : 'file-info';
        }
    }

    formatBytes(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    getCurrentFile() {
        return this.currentFile;
    }
}
