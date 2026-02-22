#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import time



def print_banner():
    print("=" * 60)
    print("                    MY  CHRONOS  DASHBOARD")
    print("=" * 60)
    print()
    print("   ██████╗██╗  ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗ ███████╗")
    print("  ██╔════╝██║  ██║██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗██╔════╝")
    print("  ██║     ███████║██████╔╝██║   ██║██╔██╗ ██║██║   ██║███████╗")
    print("  ██║     ██╔══██║██╔══██╗██║   ██║██║╚██╗██║██║   ██║╚════██║")
    print("  ╚██████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝███████║")
    print("   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝")
    print()
    print("            Initializing installer environment...")
    print()

def loading_bar(duration=3, bar_length=40):
    for i in range(bar_length + 1):
        percent = int((i / bar_length) * 100)
        bar = "█" * i + "-" * (bar_length - i)
        sys.stdout.write(f"\r            [{bar}] {percent}%")
        sys.stdout.flush()
        time.sleep(duration / bar_length)
    print("\n\n            ✔ Environment Ready.\n")
    
print_banner()
loading_bar(duration=4)


REQUIRED_PACKAGES = [
    "flask",
    "werkzeug",
    "authlib",
    "requests"
]


def ensure_pip():
    try:
        import pip
        print("✔ pip is already installed")
    except ImportError:
        print("⚠ pip not found. Installing pip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
        print("✔ pip installed successfully")

def install_packages():
    print("\nInstalling required packages...\n")
    for package in REQUIRED_PACKAGES:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package, "--break-system-packages"])
    print("\n✔ All packages installed successfully!")

# ---------------- RUN IMMEDIATELY ---------------- #

print("=" * 50)
print("        Web App Environment Installer")
print("=" * 50)
print(f"OS Detected: {platform.system()}")
print(f"Python Version: {platform.python_version()}\n")

loading_bar()

ensure_pip()
install_packages()

print("\nEnvironment setup complete!")
print("You can now run your Flask app.")

# ------------------ Helper ------------------

def run(cmd):
    print(f"\n>>> {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def get_root_drive():
    root = subprocess.check_output("findmnt -n -o SOURCE /", shell=True).decode().strip()
    return root.rstrip("0123456789")

def list_drives():
    root_drive = get_root_drive()

    result = subprocess.check_output(
        "lsblk -dpno NAME,SIZE | grep -E '/dev/sd|/dev/nvme'",
        shell=True
    ).decode().strip().split("\n")

    drives = []
    for entry in result:
        name = entry.split()[0]
        if name != root_drive:
            drives.append(entry)

    return drives

def select_drive(drives):
    if not drives:
        print("❌ No extra drives detected.")
        sys.exit(1)

    print("\nAvailable NON-SYSTEM drives:\n")
    for i, drive in enumerate(drives):
        print(f"{i+1}. {drive}")

    while True:
        try:
            choice = int(input("\nSelect drive number to format: ")) - 1
            if 0 <= choice < len(drives):
                return drives[choice].split()[0], drives[choice]
        except:
            pass
        print("Invalid selection.")

def confirm_danger(drive, drive_display):
    print("\n⚠️  DANGER ZONE ⚠️")
    print(f"You are about to PERMANENTLY ERASE: {drive_display}")
    print("ALL DATA WILL BE LOST.\n")

    typed = input(f"Type the full drive name ({drive}) to continue: ")
    if typed != drive:
        print("❌ Drive mismatch. Aborted.")
        sys.exit(1)

    confirm_word = input("Type FORMAT to confirm destruction: ")
    if confirm_word != "FORMAT":
        print("❌ Confirmation incorrect. Aborted.")
        sys.exit(1)

    print("\nFinal countdown:")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    final = input("Last chance! Proceed? (y/N): ")
    if final.lower() != "y":
        print("Aborted safely.")
        sys.exit(0)

# ------------------ Main ------------------

def main():

    if os.geteuid() != 0:
        print("❌ Run as root (sudo).")
        sys.exit(1)

    drives = list_drives()
    drive, drive_display = select_drive(drives)
    partition = drive + "1"

    confirm_danger(drive, drive_display)

    print("\n🚀 Formatting drive...\n")

    run(f"echo -e 'o\nn\np\n1\n\n\nw' | fdisk {drive}")
    run(f"mkfs.ext4 {partition}")

    mount_point = f"/mnt/{os.path.basename(drive)}1"
    run(f"mkdir -p {mount_point}")
    run(f"mount {partition} {mount_point}")

    with open("/etc/fstab", "a") as f:
        f.write(f"{partition} {mount_point} ext4 defaults,noatime 0 1\n")

    shared_dir = f"{mount_point}/shared"
    run(f"mkdir -p {shared_dir}")
    run(f"chmod -R 777 {shared_dir}")

    # -------- Samba Setup --------

    run("apt update")
    run("apt install -y samba samba-common-bin wget unzip")

    samba_config = f"""
[shared]
path={shared_dir}
writeable=Yes
create mask=0777
directory mask=0777
public=no
"""
    with open("/etc/samba/smb.conf", "a") as f:
        f.write(samba_config)

    run("systemctl restart smbd")

    run("id -u chronos || useradd -m chronos")
    run("echo 'chronos:admin' | chpasswd")
    run("echo -e 'admin\nadmin' | smbpasswd -a chronos")

    # -------- Download Chronos --------

    print("\n📥 Downloading Chronos repository...")

    temp_zip = "/tmp/chronos.zip"
    temp_extract = "/tmp/chronos_extract"

    run(f"rm -rf {temp_zip}")
    run(f"rm -rf {temp_extract}")

    run(f"wget -O {temp_zip} https://github.com/robotdjd/chronos/archive/refs/heads/main.zip")
    run(f"unzip {temp_zip} -d {temp_extract}")

    extracted_folder = f"{temp_extract}/chronos-main"

    if os.listdir(shared_dir):
        print("❌ Shared directory not empty. Aborting to prevent overwrite.")
        sys.exit(1)

    run(f"mv {extracted_folder}/* {shared_dir}/")
    run(f"chmod -R 777 {shared_dir}")

    run(f"rm -rf {temp_zip}")
    run(f"rm -rf {temp_extract}")

    # -------- Finished --------

    print("\n🎉 INSTALLATION COMPLETE!")
    print(f"Mounted at: {mount_point}")
    print("Samba Share: \\\\SERVER-IP\\shared")
    print("Username: chronos")
    print("Password: admin")

    dashboard_path = f"{shared_dir}/dashboard.sh"

    if not os.path.exists(dashboard_path):
        print("\n⚠ dashboard.sh not found. Skipping dashboard control.")
        sys.exit(0)

    run(f"chmod +x {dashboard_path}")

    print("\n✅ Installer finished.")
    
    print("=" * 60)
    print("                    MY  CHRONOS  DASHBOARD")
    print("=" * 60)
    print()
    print("   ██████╗██╗  ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗ ███████╗")
    print("  ██╔════╝██║  ██║██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗██╔════╝")
    print("  ██║     ███████║██████╔╝██║   ██║██╔██╗ ██║██║   ██║███████╗")
    print("  ██║     ██╔══██║██╔══██╗██║   ██║██║╚██╗██║██║   ██║╚════██║")
    print("  ╚██████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝███████║")
    print("   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝")
    print()
    print("            install successful ")
    print()
    

    print("                        ██████                    ")
    print("                        ██    ██                  ")
    print("                        ██    ██                  ")
    print("                        ██    ██                  ")
    print("                      ██      ██                  ")
    print("                      ██      ██                  ")
    print("                      ██      ██                  ")
    print("                    ██          ██████████████    ")
    print("                  ██                          ██  ")
    print("    ██████████  ██                            ██  ")
    print("    ██▒▒▒▒▒▒▒▒██                            ████  ")
    print("    ██▒▒▒▒▒▒▒▒██                                ██")
    print("    ██▒▒▒▒▒▒▒▒██                                ██")
    print("    ██▒▒▒▒▒▒▒▒██              yay!          ████  ")
    print("    ██▒▒▒▒▒▒▒▒██                              ██  ")
    print("    ██▒▒▒▒▒▒▒▒██                              ██  ")
    print("    ██▒▒▒▒▒▒▒▒██                          ████    ")
    print("    ██▒▒▒▒▒▒▒▒██                            ██    ")
    print("    ██████████  ██                          ██    ")
    print("                  ██████████████████████████      ")



if __name__ == "__main__":
    main()

