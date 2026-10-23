import babel from '@rolldown/plugin-babel';
import tailwindcss from '@tailwindcss/vite';
import react, { reactCompilerPreset } from '@vitejs/plugin-react';
import path from 'node:path';
import { defineConfig, loadEnv } from 'vite';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '');
  const websitePort = env.WEBSITE_PORT ? Number(env.WEBSITE_PORT) : undefined;

  return {
    envDir: '..',
    plugins: [react(), babel({ presets: [reactCompilerPreset()] }), tailwindcss()],
    server: {
      port: websitePort,
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
  };
});
