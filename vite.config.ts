import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig({
 plugins: [react(), tailwindcss()],
 // Preserve the output folder: native directory cleanup crashes on this OneDrive-backed Windows path.
 build: { emptyOutDir: false, minify: 'terser', chunkSizeWarningLimit: 900 },
});
