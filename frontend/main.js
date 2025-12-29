const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 1024,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets/icon.ico'),
    title: 'دستیار کاربر - پلتفرم تحلیل داده',
    show: false
  });

  mainWindow.loadFile('index.html');
  
  // نمایش پنجره وقتی آماده شد
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // باز کردن DevTools در حالت توسعه
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }
}

// APIهای Electron
ipcMain.handle('get-windows-user', async () => {
  return require('os').userInfo().username;
});

ipcMain.handle('select-log-path', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Log Files', extensions: ['log', 'txt'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  
  return result.canceled ? '' : result.filePaths[0];
});

ipcMain.handle('submit-ticket', async (event, ticketData) => {
  // شبیه‌سازی ارسال به بک‌اند
  console.log('تیکت ارسال شد:', ticketData);
  return { success: true, ticketId: 'TKT-' + Date.now() };
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});