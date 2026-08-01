/**
 * Delta-H WASM Loader
 * 
 * This module provides JavaScript bindings for the Delta-H codec WebAssembly implementation.
 * It handles loading the WASM module and provides a clean API for compression/decompression.
 */

let wasmInstance = null;
let wasmMemory = null;

/**
 * Initialize the WASM module
 * @returns {Promise<Object>} The WASM instance
 */
async function initDeltaH() {
  if (wasmInstance) {
    return wasmInstance;
  }

  try {
    // Load the WASM module
    const response = await fetch('/wasm/delta_h.wasm');
    const bytes = await response.arrayBuffer();
    
    // Import object for WASM
    const importObject = {
      env: {
        // Memory management functions
        memory: new WebAssembly.Memory({ initial: 256, maximum: 1024 }),
        // Logging function (optional)
        console_log: (ptr, len) => {
          const mem = new Uint8Array(wasmMemory.buffer, ptr, len);
          console.log(new TextDecoder().decode(mem));
        }
      }
    };

    // Instantiate the WASM module
    const result = await WebAssembly.instantiate(bytes, importObject);
    wasmInstance = result.instance;
    wasmMemory = wasmInstance.exports.memory;

    // Export functions
    return {
      compress: wasmInstance.exports.compress,
      decompress: wasmInstance.exports.decompress,
      free: wasmInstance.exports.free,
      getVersion: wasmInstance.exports.get_version
    };

  } catch (error) {
    console.error('Failed to initialize Delta-H WASM:', error);
    throw error;
  }
}

/**
 * Compress data using Delta-H codec
 * @param {Uint8Array} data - Input data to compress
 * @returns {Promise<Uint8Array>} Compressed data
 */
async function compressDeltaH(data) {
  const deltaH = await initDeltaH();
  
  // Allocate memory for input data
  const inputPtr = deltaH.alloc(data.length);
  new Uint8Array(wasmMemory.buffer).set(data, inputPtr);
  
  // Call compress function
  const resultPtr = deltaH.compress(inputPtr, data.length);
  
  // Get compressed data length
  const compressedLength = deltaH.get_output_size(resultPtr);
  
  // Copy compressed data to JS
  const compressedData = new Uint8Array(compressedLength);
  compressedData.set(new Uint8Array(wasmMemory.buffer).slice(resultPtr, resultPtr + compressedLength));
  
  // Free memory
  deltaH.free(resultPtr);
  deltaH.free(inputPtr);
  
  return compressedData;
}

/**
 * Decompress data using Delta-H codec
 * @param {Uint8Array} data - Compressed data
 * @returns {Promise<Uint8Array>} Decompressed data
 */
async function decompressDeltaH(data) {
  const deltaH = await initDeltaH();
  
  // Allocate memory for input data
  const inputPtr = deltaH.alloc(data.length);
  new Uint8Array(wasmMemory.buffer).set(data, inputPtr);
  
  // Call decompress function
  const resultPtr = deltaH.decompress(inputPtr, data.length);
  
  // Get decompressed data length
  const decompressedLength = deltaH.get_output_size(resultPtr);
  
  // Copy decompressed data to JS
  const decompressedData = new Uint8Array(decompressedLength);
  decompressedData.set(new Uint8Array(wasmMemory.buffer).slice(resultPtr, resultPtr + decompressedLength));
  
  // Free memory
  deltaH.free(resultPtr);
  deltaH.free(inputPtr);
  
  return decompressedData;
}

/**
 * Get codec version
 * @returns {string} Version string
 */
async function getDeltaHVersion() {
  const deltaH = await initDeltaH();
  const versionPtr = deltaH.getVersion();
  const mem = new Uint8Array(wasmMemory.buffer, versionPtr);
  return new TextDecoder().decode(mem);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initDeltaH,
    compressDeltaH,
    decompressDeltaH,
    getDeltaHVersion
  };
}

// Also export for browser usage
if (typeof window !== 'undefined') {
  window.DeltaH = {
    initDeltaH,
    compressDeltaH,
    decompressDeltaH,
    getDeltaHVersion
  };
}
