#!/usr/bin/env python3

import subprocess
import os
import sys
import time

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

    print("\nDashboard Control Menu:")
    print("1) Start Dashboard")
    print("2) Reboot Dashboard")
    print("3) Stop Dashboard")
    print("4) Skip")

    choice = input("\nSelect option: ")

    if choice == "1":
        subprocess.run(["sudo", dashboard_path, "start"])
    elif choice == "2":
        subprocess.run(["sudo", dashboard_path, "reboot"])
    elif choice == "3":
        subprocess.run(["sudo", dashboard_path, "stop"])
    else:
        print("Skipping dashboard control.")

    print("\n✅ Installer finished.")



if __name__ == "__main__":
    main()
