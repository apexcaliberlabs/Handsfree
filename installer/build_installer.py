import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def main() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    dist_dir = root_dir / "dist"
    installer_dir = root_dir / "installer"
    spec_file = root_dir / "handsfree.spec"

    print("=== [Handsfree by Apex Caliber Labs] Build Process ===")

    # 1. Clean previous build artifacts
    build_dir = root_dir / "build"
    if build_dir.exists():
        print(f"Cleaning {build_dir}...")
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
        except Exception:
            pass

    # 2. Run PyInstaller
    print("Compiling executable with PyInstaller...")
    python_exe = sys.executable
    pyinstaller_cmd = [python_exe, "-m", "PyInstaller", "--noconfirm", str(spec_file)]
    res = subprocess.run(pyinstaller_cmd, cwd=str(root_dir))
    if res.returncode != 0:
        print("[Error] PyInstaller compilation failed!")
        sys.exit(res.returncode)

    exe_target = dist_dir / "Handsfree" / "Handsfree.exe"
    if not exe_target.exists():
        print(f"[Error] Target executable not found at {exe_target}")
        sys.exit(1)

    print(f"[Success] Standalone executable compiled: {exe_target}")

    # 3. Create Portable Zip archive
    zip_path = dist_dir / "Handsfree_v1.0.0_Portable.zip"
    print(f"Packaging portable zip: {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in (dist_dir / "Handsfree").rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(dist_dir)
                zf.write(file_path, arcname)
    print(f"[Success] Portable archive created ({os.path.getsize(zip_path) // (1024*1024)} MB)")

    # 4. Search for Inno Setup compiler (ISCC)
    iscc_paths = [
        shutil.which("iscc"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    ]
    iscc_exe = None
    for p in iscc_paths:
        if p and os.path.exists(p):
            iscc_exe = p
            break

    iss_file = installer_dir / "handsfree_setup.iss"
    if iscc_exe and iss_file.exists():
        print(f"Building Windows Setup installer with Inno Setup ({iscc_exe})...")
        iscc_cmd = [iscc_exe, str(iss_file)]
        res_iscc = subprocess.run(iscc_cmd, cwd=str(installer_dir))
        if res_iscc.returncode == 0:
            setup_exe = dist_dir / "Handsfree_Setup.exe"
            print(f"[Success] Windows Setup Installer generated: {setup_exe}")
        else:
            print("[Warning] Inno Setup compilation encountered a warning.")
    else:
        print("[Info] Inno Setup compiler not found in standard paths. Portable package is ready.")

    print("\n=== Build Complete! ===")
    print(f"Executable directory: {dist_dir / 'Handsfree'}")
    print(f"Portable distribution: {zip_path}")


if __name__ == "__main__":
    main()
