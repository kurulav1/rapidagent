const { contextBridge } = require("electron")

contextBridge.exposeInMainWorld("rapidagent", {
  apiBase: "http://127.0.0.1:8000"
})
