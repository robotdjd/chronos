#!/usr/bin/env python3

import subprocess
import os
import sys
import time
import shutil

# ------------------ Helper ------------------

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
    print("            Initializing updater environment...")
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

def run(cmd):
    print(f"\n>>> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


# ------------------ Main ------------------

def main():

    if os.geteuid() != 0:
        print("❌ Run as root (sudo).")
        sys.exit(1)

    shared_dir = "/mnt/sda1/shared"  # <-- make sure this points to your shared folder
    mount_point = shared_dir  # For printing later
    protected_files = ["config.json"]  # never overwrite

    print("\n📥 Downloading Chronos repository...")

    temp_zip = "/tmp/chronos_update.zip"
    temp_extract = "/tmp/chronos_update_extract"

    # Cleanup any old temp files
    run(f"rm -rf {temp_zip}")
    run(f"rm -rf {temp_extract}")

    # Download & unzip
    run(f"wget -O {temp_zip} https://github.com/robotdjd/chronos/archive/refs/heads/main.zip")
    run(f"unzip -o {temp_zip} -d {temp_extract}")  # -o to overwrite temp conflicts

    extracted_folder = f"{temp_extract}/chronos-main"

    # -------- UPDATE --------
    for item in os.listdir(extracted_folder):
        src = os.path.join(extracted_folder, item)
        dst = os.path.join(shared_dir, item)

        # Skip protected files
        if item in protected_files and os.path.exists(dst):
            print(f"⚠️ Skipping protected file: {item}")
            continue

        # If destination exists, remove it first
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)

        # Move new file/folder
        shutil.move(src, dst)

    # Set permissions
    run(f"chmod -R 777 {shared_dir}")

    # Cleanup temp files
    run(f"rm -rf {temp_zip}")
    run(f"rm -rf {temp_extract}")

    # -------- Finished --------

    print("\n🔄 UPDATE COMPLETE! (config.json preserved)")
    print(f"Mounted at: {mount_point}")
    print("Samba Share: \\\\SERVER-IP\\shared")
    print("Username: chronos")
    print("Password: admin")
    print("stop: sudo /mnt/sda1/shared/dashboard.sh stop")
    print("reboot: sudo /mnt/sda1/shared/dashboard.sh reboot")
    print("start: sudo /mnt/sda1/shared/dashboard.sh start")
    
    dashboard_path = f"{shared_dir}/dashboard.sh"

    if not os.path.exists(dashboard_path):
        print("\n⚠ dashboard.sh not found. Skipping dashboard control.")
        sys.exit(0)

    run(f"chmod +x {dashboard_path}")



    print("\n✅ update finished.")
    
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
    print("            update successful ")
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
