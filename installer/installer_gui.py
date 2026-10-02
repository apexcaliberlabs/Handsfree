import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import winreg


class HandsfreeInstallerGUI:
    """Modern Windows 11 standalone GUI Installer for Handsfree by Apex Caliber Labs."""

    def __init__(self, source_dir: str) -> None:
        self.source_dir = Path(source_dir)
        self.root: Optional[tk.Tk] = None

        default_base = os.getenv("LOCALAPPDATA", str(Path.home()))
        self.target_dir = Path(default_base) / "Programs" / "Handsfree"

        self.create_desktop_shortcut = True
        self.create_start_menu = True
        self.enable_autostart = True
        self.launch_after_install = True

    def run(self) -> None:
        self.root = tk.Tk()
        self.root.title("Handsfree Setup - Apex Caliber Labs")
        self.root.geometry("560x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#121218")

        # Top banner
        banner = tk.Frame(self.root, bg="#1a1a26", height=70)
        banner.pack(fill="x", side="top")

        lbl_title = tk.Label(
            banner, text="Install Handsfree",
            font=("Segoe UI", 15, "bold"), fg="#00e5ff", bg="#1a1a26"
        )
        lbl_title.pack(anchor="w", padx=24, pady=(12, 2))

        lbl_by = tk.Label(
            banner, text="Touchless Vision Mouse by Apex Caliber Labs",
            font=("Segoe UI", 9), fg="#9090a8", bg="#1a1a26"
        )
        lbl_by.pack(anchor="w", padx=24, pady=(0, 10))

        # Main frame
        main_frame = tk.Frame(self.root, bg="#121218")
        main_frame.pack(fill="both", expand=True, padx=24, pady=16)

        # Destination folder
        tk.Label(main_frame, text="Destination Folder:", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#121218").pack(anchor="w", pady=(0, 4))
        dest_box = tk.Frame(main_frame, bg="#121218")
        dest_box.pack(fill="x", pady=(0, 14))

        self.var_dest = tk.StringVar(value=str(self.target_dir))
        entry_dest = tk.Entry(dest_box, textvariable=self.var_dest, font=("Segoe UI", 9), bg="#1e1e2c", fg="#ffffff", insertbackground="#00e5ff", relief="flat")
        entry_dest.pack(side="left", fill="x", expand=True, ipady=4)

        btn_browse = tk.Button(dest_box, text="Browse...", font=("Segoe UI", 8), bg="#2d2d40", fg="#00e5ff", relief="flat", command=self._browse_dir)
        btn_browse.pack(side="right", padx=(8, 0))

        # Options
        tk.Label(main_frame, text="Install Options:", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#121218").pack(anchor="w", pady=(6, 4))

        self.var_desktop = tk.BooleanVar(value=True)
        cb_desk = tk.Checkbutton(main_frame, text="Create Desktop Shortcut", variable=self.var_desktop, font=("Segoe UI", 9), bg="#121218", fg="#d0d0e0", selectcolor="#1e1e2c", activebackground="#121218")
        cb_desk.pack(anchor="w", pady=2)

        self.var_startmenu = tk.BooleanVar(value=True)
        cb_sm = tk.Checkbutton(main_frame, text="Create Start Menu Shortcut", variable=self.var_startmenu, font=("Segoe UI", 9), bg="#121218", fg="#d0d0e0", selectcolor="#1e1e2c", activebackground="#121218")
        cb_sm.pack(anchor="w", pady=2)

        self.var_autostart = tk.BooleanVar(value=True)
        cb_auto = tk.Checkbutton(main_frame, text="Launch automatically on Windows startup", variable=self.var_autostart, font=("Segoe UI", 9), bg="#121218", fg="#d0d0e0", selectcolor="#1e1e2c", activebackground="#121218")
        cb_auto.pack(anchor="w", pady=2)

        self.var_launch = tk.BooleanVar(value=True)
        cb_lnch = tk.Checkbutton(main_frame, text="Launch Handsfree immediately after setup", variable=self.var_launch, font=("Segoe UI", 9), bg="#121218", fg="#d0d0e0", selectcolor="#1e1e2c", activebackground="#121218")
        cb_lnch.pack(anchor="w", pady=2)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode="determinate")
        self.progress.pack(fill="x", pady=(14, 0))

        self.lbl_status = tk.Label(main_frame, text="Ready to install.", font=("Segoe UI", 8), fg="#707088", bg="#121218")
        self.lbl_status.pack(anchor="w", pady=(4, 0))

        # Bottom buttons
        bottom = tk.Frame(self.root, bg="#1a1a26", height=50)
        bottom.pack(fill="x", side="bottom")

        self.btn_install = tk.Button(
            bottom, text="Install Now", font=("Segoe UI", 9, "bold"),
            bg="#00bcd4", fg="#000000", activebackground="#00e5ff",
            relief="flat", width=14, command=self._do_install
        )
        self.btn_install.pack(side="right", padx=24, pady=10)

        self.btn_cancel = tk.Button(
            bottom, text="Cancel", font=("Segoe UI", 9),
            bg="#2a2a3c", fg="#ffffff", relief="flat", width=10,
            command=self.root.destroy
        )
        self.btn_cancel.pack(side="right", padx=(0, 10), pady=10)

        self.root.mainloop()

    def _browse_dir(self) -> None:
        sel = filedialog.askdirectory(initialdir=self.var_dest.get(), title="Select Install Folder")
        if sel:
            self.var_dest.set(sel)

    def _do_install(self) -> None:
        self.btn_install.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")
        target = Path(self.var_dest.get())

        try:
            self.lbl_status.configure(text="Copying program files...")
            self.progress["value"] = 30
            self.root.update()

            target.mkdir(parents=True, exist_ok=True)
            # Copy all files from source
            for item in self.source_dir.glob("*"):
                dest_item = target / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest_item)

            self.progress["value"] = 65
            self.lbl_status.configure(text="Creating shortcuts...")
            self.root.update()

            exe_path = target / "Handsfree.exe"

            # Create Windows shortcuts using VBScript
            if self.var_desktop.get() and exe_path.exists():
                desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
                self._create_shortcut(str(exe_path), str(desktop / "Handsfree.lnk"))

            if self.var_startmenu.get() and exe_path.exists():
                start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Apex Caliber Labs"
                start_menu.mkdir(parents=True, exist_ok=True)
                self._create_shortcut(str(exe_path), str(start_menu / "Handsfree.lnk"))

            # Registry startup toggle
            if self.var_autostart.get() and exe_path.exists():
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                    with key:
                        winreg.SetValueEx(key, "HandsfreeApexCaliberLabs", 0, winreg.REG_SZ, f'"{exe_path}" --background')
                except Exception:
                    pass

            # Register in Windows Settings Apps / Uninstall
            self._register_uninstall(target, exe_path)

            self.progress["value"] = 100
            self.lbl_status.configure(text="Installation completed successfully!", fg="#00e5ff")
            self.root.update()

            # Launch app if selected
            if self.var_launch.get() and exe_path.exists():
                import subprocess
                subprocess.Popen([str(exe_path)])

            messagebox.showinfo("Installation Complete", f"Handsfree has been successfully installed to:\n{target}")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Installation Error", f"Installation failed: {e}")
            self.btn_install.configure(state="normal")
            self.btn_cancel.configure(state="normal")

    def _create_shortcut(self, target_path: str, link_path: str) -> None:
        """Creates Windows .lnk shortcut via VBScript without external packages."""
        vbs_script = (
            f'Set oWS = WScript.CreateObject("WScript.Shell")\n'
            f'sLinkFile = "{link_path}"\n'
            f'Set oLink = oWS.CreateShortcut(sLinkFile)\n'
            f'oLink.TargetPath = "{target_path}"\n'
            f'oLink.WorkingDirectory = "{Path(target_path).parent}"\n'
            f'oLink.Save\n'
        )
        tmp_vbs = Path(os.environ["TEMP"]) / "create_lnk.vbs"
        try:
            with open(tmp_vbs, "w", encoding="utf-8") as f:
                f.write(vbs_script)
            os.system(f'cscript //nologo "{tmp_vbs}"')
        finally:
            if tmp_vbs.exists():
                try:
                    os.remove(tmp_vbs)
                except Exception:
                    pass

    def _register_uninstall(self, install_dir: Path, exe_path: Path) -> None:
        """Registers entry in Windows Add/Remove Programs."""
        try:
            uninst_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Handsfree"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninst_key)
            with key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Handsfree by Apex Caliber Labs")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Apex Caliber Labs")
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe_path))
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        except Exception as e:
            print(f"[Installer] Registry warning: {e}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / "dist" / "Handsfree")
    installer = HandsfreeInstallerGUI(src)
    installer.run()
