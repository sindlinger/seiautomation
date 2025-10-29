import { contextBridge } from 'electron';

contextBridge.exposeInMainWorld('seiautomation', {
  version: process.env.npm_package_version,
});
