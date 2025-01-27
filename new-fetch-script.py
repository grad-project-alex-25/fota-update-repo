import os
import re
import subprocess
import sys
import os

# Get the current working directory
current_directory = os.getcwd()

# Define constants
FILE_NAME = "UPDATES_FLAGS_FILE"
OUTPUT_FILE = "test"
ROUTE_TABLE = "ROUTE_TABLE"

# Helper function to run shell commands and return output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.strip()}")
        sys.exit(1)

# Ensure we are in a Git repository
try:
    run_command("git rev-parse --is-inside-work-tree")
except SystemExit:
    print("Error: This is not a git repository.")
    sys.exit(1)

# Fetch the latest changes from the remote repository
print("Fetching updates from the remote repository...")
run_command("git fetch origin main")

# Generate the diff and save it to the output file
print(f"Generating the diff and saving it to '{OUTPUT_FILE}'...")
with open(OUTPUT_FILE, "w") as output_file:
    diff = run_command("git diff HEAD origin/main")
    output_file.write(diff)

# Confirm completion
if not os.path.isfile(OUTPUT_FILE):
    print(f"Error: File '{OUTPUT_FILE}' does not exist.")
    sys.exit(1)
print(f"Done! The diff has been saved to '{OUTPUT_FILE}'.")

# Process the diff file
accept = 0 
with open(OUTPUT_FILE, "r") as output_file:
    for line in output_file:
        mcu_match = re.match(r"^\+MCU-([1-9])=([1-9]|1[0-9]|20)\.([0-9]|[1-3][0-9]|40)\.([0-9]|[1-5][0-9]|60)", line)
        zonal_match = re.match(r"^\+ZONAL-([1-9])=([1-9]|1[0-9]|20)\.([0-9]|[1-3][0-9]|40)\.([0-9]|[1-5][0-9]|60)", line)
        center_match = re.match(r"^\+CENTER-([1-9])=([1-9]|1[0-9]|20)\.([0-9]|[1-3][0-9]|40)\.([0-9]|[1-5][0-9]|60)", line)

        if mcu_match:
            m_id = mcu_match.group(1)
            mcu_version = f"{mcu_match.group(2)}.{mcu_match.group(3)}.{mcu_match.group(4)}"
            maj_v = mcu_match.group(2) 
            min_v = mcu_match.group(3)
            print(f"Processing MCU-{m_id} with version {mcu_version}")

            with open(ROUTE_TABLE, "r") as route_table_file:
                for route_line in route_table_file:
                    zonal_match = re.match(rf"^MCU-\[{m_id}]:ZONAL-([1-9])", route_line)
                    if zonal_match:
                        zonal_id = zonal_match.group(1)
                        print(f"From zonal={zonal_id}")
                       

            run_command(f"git checkout origin/main -- MCU-{m_id}")
            
            print("Done! MCU update pulled successfully.")
            result=subprocess.run(["python3", "/home/abokhalil/Desktop/Embedded/fota-scripts/send-update.py", zonal_id, maj_v, min_v])
            if (result.returncode == 0x55):
                print("The user accepted the update.")
                subprocess.run(["python3", f"{current_directory}/../Embedded/fota-scripts/Send_bin.py", f"{current_directory}/MCU-{m_id}/update.bin", zonal_id, maj_v, min_v])
            elif(result.returncode == 0x66):
                print("The user rejected the update.")
            
        elif zonal_match:
            z_id = zonal_match.group(1)
            z_version = f"{zonal_match.group(2)}.{zonal_match.group(3)}.{zonal_match.group(4)}"
            print(f"Processing ZONAL-{z_id} with version {z_version}")

        elif center_match:
            c_id = center_match.group(1)
            c_version = f"{center_match.group(2)}.{center_match.group(3)}.{center_match.group(4)}"
            print(f"Processing CENTER-{c_id} with version {c_version}")

