const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getWindowsUser: () => ipcRenderer.invoke('get-windows-user'),
  selectLogPath: () => ipcRenderer.invoke('select-log-path'),
  submitTicket: (ticketData) => ipcRenderer.invoke('submit-ticket', ticketData)
});