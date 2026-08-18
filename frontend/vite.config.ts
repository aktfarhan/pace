import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
        alias: { '@': path.resolve(import.meta.dirname, './src') },
    },
    // The port backend/app.py allows through CORS
    server: { port: 3000, strictPort: true },
    preview: { port: 3000 },
});
