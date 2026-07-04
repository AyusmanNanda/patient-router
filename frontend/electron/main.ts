import { app, BrowserWindow } from "electron";
import path from "path";
import { fileURLToPath } from "url";
import os from "os";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.setPath("userData", path.join(os.homedir(), ".patient-router"));

let mainWindow: BrowserWindow | null = null;

function getIndexPath(): string {
    if (app.isPackaged) {
        return path.join(process.resourcesPath, "app.asar", "dist", "index.html");
    }

    return path.join(__dirname, "../dist/index.html");
}

function createWindow(): void {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        backgroundColor: "#ffffff",
        icon: path.join(__dirname, "icon.png"),
        titleBarStyle: "hiddenInset",
        webPreferences: {
            contextIsolation: true,
            nodeIntegration: false,
        }
    });

    mainWindow.removeMenu();

    const indexPath: string = getIndexPath();

    mainWindow.loadFile(indexPath);
}

app.whenReady().then(createWindow);

app.on("activate", (): void => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on("window-all-closed", (): void => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});