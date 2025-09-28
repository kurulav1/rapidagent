const { app, BrowserWindow } = require("electron")
const path = require("path")

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  })

  // In dev, load Vite dev server
  if (process.env.ELECTRON_DEV) {
    mainWindow.loadURL("http://localhost:5173")
  } else {
    // In prod, load built frontend
    mainWindow.loadFile(path.join(__dirname, "../frontend/dist/index.html"))
  }
}

app.whenReady().then(() => {
  createWindow()
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit()
})
