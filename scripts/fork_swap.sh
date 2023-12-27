#!/bin/bash
#
# Script Name: fork_swap.sh
# Script version
SCRIPT_VERSION="2.3.3"
#
# Author: swish865
#
# Description: 
#   This script is a utility designed to manage multiple forks of the OpenPilot project 
#   installed on your comma device. It allows users to effortlessly switch between various forks, 
#   clone new ones from GitHub repositories, and even delete unwanted forks. The script performs
#   validations, backups, and handles log rotation.
#
# Prerequisites:
#   - Script must be run as root.
#   - Necessary directories must exist.
#   - Assumes OpenPilot is installed in /data/openpilot.
#
# Usage:
#   sudo ./fork_swap.sh
#
# Optional Parameters: None
#
# Logging:
#   Logs are written to /data/fork_swap.log and rotated automatically.
#
# Notes:
#   - Do not run this script while OpenPilot is engaged.
#   - Ensure you have a backup of your data before running this script.
#
# License: 
#   This script is released under the MIT license.


# Configuration variables for directories, files, and constants
OPENPILOT_DIR="/data/openpilot"
FORKS_DIR="/data/forks"
CURRENT_FORK_FILE="/data/current_fork.txt"
PARAMS_PATH="/data/params"
MAX_RETRIES=3
LOG_FILE="/data/fork_swap.log"
MAX_LOG_SIZE=1048576  # Maximum log size in bytes (1MB)

# Colors for better UI
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
RESET=$(tput sgr0)

# Function to rotate logs
rotate_logs() {
    local log_size=$(stat -c %s "$LOG_FILE")
    if [ $log_size -ge $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "$LOG_FILE.old"
        echo "Log rotated on $(date)" > "$LOG_FILE"
    fi
}

# Function to log general info messages
log_info() {
    rotate_logs  # Check if log needs to be rotated
    echo "$1" | tee -a "$LOG_FILE"
}

# Function to log error messages
log_error() {
    rotate_logs  # Check if log needs to be rotated
    echo "----- Error on $(date) -----"
    echo "$1" | tee -a "$LOG_FILE"
}

# Function to check for updates to the fork_swap.sh script
check_for_script_updates() {
    # Hardcoded script path and repo details
    script_path="/data/openpilot/scripts/fork_swap.sh"
    repo_url="https://github.com/james5294/openpilot.git"
    repo_branch="master"

    echo "Checking for updates to fork_swap.sh..."

    # Create a temporary directory to check for updates without disturbing the current setup
    tmp_dir=$(mktemp -d -t fork_swap_update_XXXXXX)
    git clone --depth 1 -b $repo_branch $repo_url $tmp_dir > /dev/null 2>&1

    # Compare the local and remote versions of fork_swap.sh
    diff $script_path $tmp_dir/scripts/fork_swap.sh > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Update available for fork_swap.sh.${RESET}"
        UPDATE_AVAILABLE=1
    else
        echo -e "${GREEN}fork_swap.sh is up to date.${RESET}"
        UPDATE_AVAILABLE=0
    fi

    # Clean up temporary directory
    rm -rf $tmp_dir
}

# Function to update to the fork_swap.sh script
update_script() {
    # Clone the repository to a temporary directory
    tmp_dir=$(mktemp -d -t fork_swap_update_XXXXXX)
    git clone --depth 1 -b $repo_branch $repo_url $tmp_dir > /dev/null 2>&1
    
    # Check if the updated script exists in the temporary directory
    if [ -f "$tmp_dir/scripts/fork_swap.sh" ]; then
        # Replace the current script with the updated one
        cp "$tmp_dir/scripts/fork_swap.sh" "$script_path"
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}Script updated successfully! Restarting the script to use the updated version...${RESET}"
            
            # Clean up the temporary directory
            rm -rf $tmp_dir

            # Relaunch the script
            exec sudo bash "$script_path"
            exit 0  # This exit is redundant as exec replaces the current process, but it's good practice to include it.
        else
            echo -e "${RED}Error while updating the script.${RESET}"
        fi
    else
        echo -e "${RED}Updated script not found in the repository.${RESET}"
    fi

    # Clean up the temporary directory
    rm -rf $tmp_dir
}

# Function to check for updates for a given fork
check_for_fork_updates() {
    local fork_dir="$FORKS_DIR/$1/openpilot"
    local update_status=0  # 0 means no update, 1 means update available

    # If the fork being checked is the active one, change the directory to check
    if [[ "$1" == "$CURRENT_FORK_NAME" ]]; then
        fork_dir="$OPENPILOT_DIR"
    fi
    
    # Change to the fork directory
    pushd "$fork_dir" > /dev/null
    
    # Fetch the latest changes without applying them and suppress output
    git fetch > /dev/null 2>&1

    # Compare the local branch with the remote branch
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse @{u} 2>/dev/null)

    if [ "$local_commit" != "$remote_commit" ]; then
        update_status=1
    fi

    # Return to the previous directory
    popd > /dev/null

    return $update_status
}

# Function to get available disk space
get_available_disk_space() {
    DISK_SPACE_OUTPUT=$(df -h /data)
    echo "Debug: df -h /data returns: $DISK_SPACE_OUTPUT"

    DISK_SPACE=$(echo "$DISK_SPACE_OUTPUT" | awk 'NR==2 {print $4}')
    echo "Debug: Extracted disk space is: $DISK_SPACE"

    echo -e "${MAGENTA}Available Disk Space: ${RESET}${YELLOW}$DISK_SPACE${RESET}"
}

# Function to ensure fork_swap.sh exists in the current fork's directory and is up-to-date
ensure_fork_swap_script() {
    local target_script="$OPENPILOT_DIR/scripts/fork_swap.sh"
    local source_script="$FORKS_DIR/james5294/openpilot/scripts/fork_swap.sh"
    
    log_info "Ensuring fork_swap.sh is up-to-date in current fork's scripts directory..."
    cp "$source_script" "$target_script"
    
    if [[ $? -eq 0 ]]; then
        log_info "fork_swap.sh copied/updated successfully in the current fork's scripts directory."
    else
        log_error "Error while copying/updating fork_swap.sh in the current fork's scripts directory."
    fi
}

# Function to validate a fork name or other key variables
validate_variable() {
    if [ -z "$1" ]; then
        log_error "Variable is empty. Exiting."
        exit 1
    fi
}

# Function to validate fork name and avoid special characters
validate_input() {
    if [[ $1 =~ [^a-zA-Z0-9_-] ]]; then
        echo "Error: Invalid input. Only alphanumeric characters, dashes, and underscores are allowed." | tee -a $LOG_FILE
        return 1
    fi
    return 0
}

# Function to validate the format of GitHub repository URL
validate_url() {
    if [[ ! $1 =~ ^https://github.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+.git$ ]]; then
        echo "Error: Invalid URL format." | tee -a $LOG_FILE
        return 1
    fi
    return 0
}

# Function to retry operations a specified number of times (for network operations)
retry_operation() {
    local retries=$MAX_RETRIES
    until "$@"; do
        retries=$((retries - 1))
        if [ $retries -lt 1 ]; then
            echo "Operation failed after $MAX_RETRIES attempts. Exiting." | tee -a $LOG_FILE
            cleanup
            exit 1
        fi
        echo "Operation failed. Retrying... ($retries attempts remaining)" | tee -a $LOG_FILE
        sleep 2
    done
}

# Call the script update check function at the beginning
check_for_script_updates

# Update the available disk space first
    get_available_disk_space

# Function to display the initial welcome screen
display_welcome_screen() {
    # Determine the current active fork
    CURRENT_FORK_NAME=""
    if [ -f "$CURRENT_FORK_FILE" ] && [ -n "$(cat "$CURRENT_FORK_FILE")" ]; then
        CURRENT_FORK_NAME=$(cat "$CURRENT_FORK_FILE")
    else
        echo "Unknown active fork. Please provide the name:" | tee -a $LOG_FILE
        read CURRENT_FORK_NAME
        validate_input "$CURRENT_FORK_NAME" || exit 1
        echo "$CURRENT_FORK_NAME" > "$CURRENT_FORK_FILE" | tee -a $LOG_FILE
    fi

    # Clear the screen and display the welcome message
    clear
    echo -e "${YELLOW}==========================================================${RESET}"
    echo -e "${RED}                  **Fork Swap Utility**                   ${RESET}"
    echo "                         v$SCRIPT_VERSION                     "
    echo -e "${YELLOW}==========================================================${RESET}"
    echo "    This utility allows you to switch between different"
    echo "              forks of the OpenPilot project."
    if [ $UPDATE_AVAILABLE -eq 1 ]; then
        echo -e "${RED}         *An update is available for fork_swap.sh*${RESET}"
    else
        echo -e "${GREEN}                *This script is up to date*${RESET}"
    fi
        echo ""
        echo ""
    echo -e "${CYAN}Current Active Fork:${RESET}" "$CURRENT_FORK_NAME" | tee -a $LOG_FILE
    echo -e "${MAGENTA}Available Disk Space: ${RESET}${YELLOW}$DISK_SPACE${RESET}"
    echo ""
    # Display available forks
    echo -e "${GREEN}Available forks:${RESET}"
    echo ""
    for fork in $(ls "$FORKS_DIR"); do
        if check_for_fork_updates "$fork"; then
            echo "$fork - ${CYAN}(update available)${RESET}"

        else
            echo "$fork"
        fi
    done
    echo ""
    echo "Please select an option:"
    echo ""
    echo "          1. ""${GREEN}Fork name ${RESET}""from above you want to switch to."
    echo "          2. ""${MAGENTA}'Clone a new fork'${RESET}" "to clone a new fork." | tee -a $LOG_FILE
    echo -e "          3. ""${RED}'Delete a fork'${RESET} to delete an available fork." | tee -a $LOG_FILE
    echo -e "          4. ""${RED}'Exit'${RESET} to close the script." | tee -a $LOG_FILE
    if [ $UPDATE_AVAILABLE -eq 1 ]; then
    echo -e "          5. Type ${GREEN}'Update script'${RESET} to update fork_swap.sh." | tee -a $LOG_FILE
    fi
    echo -e "${YELLOW}==========================================================${RESET}"
}

# Updates the current fork to the specified fork and logs the result.
update_current_fork() {
    if [ -z "$1" ]; then
        log_error "No fork name provided to update_current_fork function."
        return
    fi

    log_info "Attempting to update the current fork to: $1"
    
    # Try to write the fork name to the CURRENT_FORK_FILE and capture any error message
    ERROR_MSG=$(echo "$1" > "$CURRENT_FORK_FILE" 2>&1)
    
    # Check if the operation was successful by reading back the file
    CURRENT_FORK=$(cat "$CURRENT_FORK_FILE")
    
    log_info "Retrieved current fork value from file: $CURRENT_FORK"
    
    if [ "$CURRENT_FORK" == "$1" ]; then
        log_info "Current fork updated successfully to: $1"
    else
        log_error "Mismatch detected. Expected fork: $1, but found: $CURRENT_FORK. Error during write (if any): $ERROR_MSG"
    fi
}

# Ensure necessary directories and files exist
[ ! -d "$FORKS_DIR" ] && mkdir -p "$FORKS_DIR" && echo "Created directory: $FORKS_DIR" | tee -a $LOG_FILE
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE" && echo "Log file created at: $LOG_FILE" | tee -a $LOG_FILE
[ ! -f "$CURRENT_FORK_FILE" ] && touch "$CURRENT_FORK_FILE" && echo "No active fork. Created file: $CURRENT_FORK_FILE" | tee -a $LOG_FILE

# Create or append to the log file
echo "----- Log Entry on $(date) -----" >> $LOG_FILE

# Locking mechanism to prevent concurrent runs
#lockfile="/tmp/fork_swap.lock"

# Function to remove lockfile
#remove_lockfile() {
#    rm -f "$lockfile"
#}

# Locking mechanism to prevent concurrent runs
#lockfile="/tmp/fork_swap.lock"

# Set trap to remove lockfile upon any exit
#trap remove_lockfile EXIT

# Check if an old lockfile exists and if the process is still running
#if [ -f "$lockfile" ]; then
#    stored_pid=$(cat "$lockfile")
#    # Check if process is actually running
#    if kill -0 "$stored_pid" 2>/dev/null; then
#        echo "Another instance of the script is running. Exiting." | tee -a $LOG_FILE
#        exit 1
#    else
#        # Old lockfile, remove
#        rm -f "$lockfile"
#    fi
#fi

# Create a new lockfile
#if ( set -o noclobber; echo "$$" > "$lockfile") 2> /dev/null; then
#    :
#else
#    echo "Another instance of the script is running. Exiting." | tee -a $LOG_FILE
#    exit 1
#fi

# Check if script is being run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" | tee -a $LOG_FILE
   exit 1
fi

# Cleanup function to restore previous state in case of errors
cleanup() {
    echo "Cleaning up..." | tee -a $LOG_FILE

    # Restoring the previous OpenPilot instance
    if [ -d "$FORKS_DIR/$CURRENT_FORK_NAME/openpilot" ] && [ ! -d "$OPENPILOT_DIR" ]; then
        mv "$FORKS_DIR/$CURRENT_FORK_NAME/openpilot" "$OPENPILOT_DIR"
        if [[ $? -eq 0 ]]; then
            log_info "Successfully restored $CURRENT_FORK_NAME to OpenPilot directory."
        else
            log_error "Error while restoring $CURRENT_FORK_NAME to OpenPilot directory."
        fi
    fi

    # Restoring original params (assuming a backup was made)
    if [ -d "$FORKS_DIR/$CURRENT_FORK_NAME/params" ]; then
        cp -r "$FORKS_DIR/$CURRENT_FORK_NAME/params" "$PARAMS_PATH"
        if [[ $? -eq 0 ]]; then
            log_info "Successfully restored params for $CURRENT_FORK_NAME."
        else
            log_error "Error while restoring params for $CURRENT_FORK_NAME."
        fi
    fi

    # Remove any temporary directories or files if they exist
    rm -rf "$FORKS_DIR/temp"
    if [[ $? -eq 0 ]]; then
        log_info "Temporary directories or files removed successfully."
    else
        log_error "Error while removing temporary directories or files."
    fi

    echo "Cleanup completed." | tee -a $LOG_FILE
}

# Trap signals to ensure cleanup happens in case of errors or interruptions
trap cleanup ERR SIGINT

# Display the welcome screen first
display_welcome_screen

# Main loop for fork switching or cloning logic
while true; do
    read -p "Your choice: " fork
     # Check if user input starts with "Update"
    if [[ $fork == Update* ]]; then
        # Extract fork name from the input
        fork_name_to_update=${fork#Update }
        
        # Check if the fork exists and has an update available
        if [ -d "$FORKS_DIR/$fork_name_to_update/openpilot" ] && check_for_fork_updates "$fork_name_to_update"; then
            # Ask user for confirmation
            read -p "Do you want to update the fork $fork_name_to_update? (y/n) " confirm_update
            if [[ "$confirm_update" == "y" ]]; then
                # Initiate the update
                cd "$FORKS_DIR/$fork_name_to_update/openpilot"
                git pull
                echo "Fork $fork_name_to_update has been updated."
                cd -
            else
                echo "Update canceled."
            fi
        elif [ -d "$FORKS_DIR/$fork_name_to_update/openpilot" ]; then
            echo "No updates available for $fork_name_to_update."
        else
            echo "The fork $fork_name_to_update does not exist."
        fi

        # Continue to the next iteration of the loop
        continue
    fi
    case "$fork" in
    "Clone a new fork")
        read -p "Enter a name for the new fork: " new_fork_name
        validate_input "$new_fork_name" || exit 1
            if [ -d "$FORKS_DIR/$new_fork_name" ]; then
                read -p "A fork with this name already exists. Are you sure you want to overwrite it? (y/n) " overwrite_choice
                if [[ "$overwrite_choice" != "y" ]]; then
                    echo "Exiting without making changes."
                    exit 0
                fi
            fi
            read -p "Enter the URL of the fork to clone: " fork_url
            validate_url "$fork_url" || exit 1

            # Prompt for the branch to clone     
            read -p "Enter the branch name (leave empty for default branch): " branch_name

            # Check if the openpilot directory already exists in the target fork directory and delete it if it does
            if [ -d "$FORKS_DIR/$new_fork_name/openpilot" ]; then
                rm -rf "$FORKS_DIR/$new_fork_name/openpilot"
                if [[ $? -eq 0 ]]; then
                    log_info "Existing openpilot directory for $new_fork_name deleted."
                else
                    log_error "Error while deleting existing openpilot directory for $new_fork_name."
                fi
            fi

            # Clone the fork with the specified branch (if provided) and retry if necessary
            if [ -z "$branch_name" ]; then
                retry_operation git clone --single-branch --recurse-submodules "$fork_url" "$FORKS_DIR/$new_fork_name/openpilot"
            else
                retry_operation git clone -b "$branch_name" --single-branch --recurse-submodules "$fork_url" "$FORKS_DIR/$new_fork_name/openpilot"
            fi

            # Set ownership for the cloned directory
            sudo chown -R comma:comma "$FORKS_DIR/$new_fork_name/openpilot"
            if [[ $? -eq 0 ]]; then
                log_info "Permissions for cloned fork adjusted."
            else
                log_error "Error while adjusting permissions for cloned fork."
            fi
            
            # Validate variable
            validate_variable "$CURRENT_FORK_NAME"

            # Backup current params
            if [ -d "$PARAMS_PATH" ]; then
                mkdir -p "$FORKS_DIR/$CURRENT_FORK_NAME/params"
                cp -r "$PARAMS_PATH"/* "$FORKS_DIR/$CURRENT_FORK_NAME/params/"
                if [[ $? -eq 0 ]]; then
                    log_info "Params for $CURRENT_FORK_NAME backed up."
                else
                    log_error "Error while backing up params for $CURRENT_FORK_NAME."
                fi
            fi

            # Backup the current openpilot directory to the current fork's directory
            mv "$OPENPILOT_DIR" "$FORKS_DIR/$CURRENT_FORK_NAME/openpilot"
            if [[ $? -eq 0 ]]; then
                log_info "Openpilot directory for $CURRENT_FORK_NAME backed up."
            else
                log_error "Error while backing up openpilot directory for $CURRENT_FORK_NAME."
            fi

            # Move the newly cloned fork to the openpilot directory
            mv "$FORKS_DIR/$new_fork_name/openpilot" "$OPENPILOT_DIR"
            if [[ $? -eq 0 ]]; then
                log_info "Newly cloned fork moved to openpilot directory."
            else
                log_error "Error while moving newly cloned fork to openpilot directory."
            fi
            
            # Update CURRENT_FORK_NAME right after getting the new fork name.
            CURRENT_FORK_NAME="$new_fork_name"
            
            # Update the current fork file
            echo "$new_fork_name" > "$CURRENT_FORK_FILE"
            if [[ $? -eq 0 ]]; then
                log_info "Current fork updated to $CURRENT_FORK_NAME."
            else
                log_error "Error while updating current fork to $CURRENT_FORK_NAME."
            fi

            # Adjust permissions for the new openpilot directory
            sudo chown -R comma:comma "$OPENPILOT_DIR"
            if [[ $? -eq 0 ]]; then
                log_info "Permissions for openpilot directory adjusted."
            else
                log_error "Error while adjusting permissions for openpilot directory."
            fi

            # Ensure fork_swap.sh is present in the cloned fork
            ensure_fork_swap_script

            chmod +x $OPENPILOT_DIR/scripts/fork_swap.sh
            if [[ $? -eq 0 ]]; then
                log_info "Permissions for fork_swap.sh adjusted."
            else
                log_error "Error while adjusting permissions for fork_swap.sh."
            fi

            # Inform the user and reboot
            echo "Switched to new fork named $CURRENT_FORK_NAME. Rebooting..."
            sudo reboot
            ;;
    "Delete a fork")
        read -p "Enter the name of the fork to delete: " delete_fork_name
        validate_input "$delete_fork_name" || exit 1
        if [ -d "$FORKS_DIR/$delete_fork_name" ]; then
            read -p "Are you sure you want to delete $delete_fork_name? This cannot be undone. (y/n) " delete_choice
            if [[ "$delete_choice" == "y" ]]; then
                rm -rf "$FORKS_DIR/$delete_fork_name"
                if [[ $? -eq 0 ]]; then
                    log_info "Successfully deleted the fork: $delete_fork_name."
                    
                    # Refresh the welcome screen
                    display_welcome_screen
                else
                    log_error "Error while deleting the fork: $delete_fork_name."
                fi
            else
                echo "Exiting without deleting the fork."
            fi
        else
            echo "The specified fork does not exist."
        fi
        ;;
    "Exit")
        echo "Exiting the script."
        exit 0
        ;;
    "Update script")
        update_script
        ;;
    *)
            if [ -d "$FORKS_DIR/$fork/openpilot" ]; then
                read -p "Switching to $fork. Are you sure? (y/n) " switch_choice
                if [[ "$switch_choice" == "y" ]]; then
                    
                    # Validate variable
                    validate_variable "$CURRENT_FORK_NAME"

                    # Backup current params
                    if [ -d "$PARAMS_PATH" ]; then
                        mkdir -p "$FORKS_DIR/$CURRENT_FORK_NAME/params"
                        cp -r "$PARAMS_PATH" "$FORKS_DIR/$CURRENT_FORK_NAME/params"
                        if [[ $? -eq 0 ]]; then
                            log_info "Params for $CURRENT_FORK_NAME backed up."
                        else
                            log_error "Error while backing up params for $CURRENT_FORK_NAME."
                        fi
                    fi

                    # Check if the target directory exists in the current fork's directory and delete it if it does
                    if [ -d "$FORKS_DIR/$CURRENT_FORK_NAME/openpilot" ]; then
                        rm -rf "$FORKS_DIR/$CURRENT_FORK_NAME/openpilot"
                        if [[ $? -eq 0 ]]; then
                            log_info "Openpilot directory for $CURRENT_FORK_NAME deleted."
                        else
                            log_error "Error while deleting openpilot directory for $CURRENT_FORK_NAME."
                        fi
                    fi

                    # Move the current openpilot directory to the current fork's directory
                    log_info "Starting move operation..."
                    log_info "Moving from: $OPENPILOT_DIR"
                    log_info "Moving to: $FORKS_DIR/$CURRENT_FORK_NAME/"
                    mv "$OPENPILOT_DIR" "$FORKS_DIR/$CURRENT_FORK_NAME/"
                    
                    # Check the result of the move operation
                    if [[ $? -eq 0 ]]; then
                        log_info "Openpilot directory moved to $CURRENT_FORK_NAME's directory."
                    else
                        log_error "Error while moving openpilot directory to $CURRENT_FORK_NAME's directory."
                    fi

                    # Check if the openpilot directory exists in /data/ and delete it if it does
                    if [ -d "$OPENPILOT_DIR" ]; then
                        log_info "Attempting to delete directory: $OPENPILOT_DIR"
                        
                        # Try to delete the directory and capture any error message
                        ERROR_MSG=$(sudo rm -rf "$OPENPILOT_DIR" 2>&1)
                        
                        # Check if the directory was successfully deleted
                        if [ ! -d "$OPENPILOT_DIR" ]; then
                            log_info "Openpilot directory in /data/ deleted successfully."
                        else
                            log_error "Error while deleting openpilot directory in /data/. Error: $ERROR_MSG"
                        fi
                    else
                        log_info "Openpilot directory in /data/ does not exist. Skipping deletion."
                    fi

                    # Move the selected fork's openpilot directory to /data/
                    log_info "Starting move operation..."
                    log_info "Moving from: $FORKS_DIR/$fork/openpilot"
                    log_info "Moving to: $OPENPILOT_DIR"
                    mv "$FORKS_DIR/$fork/openpilot" "$OPENPILOT_DIR"
                    
                    # Check the result of the move operation
                    if [[ $? -eq 0 ]]; then
                        log_info "Selected fork's openpilot directory moved to /data/."
                    else
                        log_error "Error while moving selected fork's openpilot directory to /data/."
                    fi

                    # Update the current fork file
                    update_current_fork "$fork"

                    # Restore the params for the selected fork
                    if [ -d "$FORKS_DIR/$fork/params" ]; then
                        cp -r "$FORKS_DIR/$fork/params" "$PARAMS_PATH"
                        if [[ $? -eq 0 ]]; then
                            log_info "Params for $fork restored."
                        else
                            log_error "Error while restoring params for $fork."
                        fi
                    fi

                    # Adjust permissions for the new openpilot directory
                    sudo chown -R comma:comma "$OPENPILOT_DIR"
                    if [[ $? -eq 0 ]]; then
                        log_info "Permissions for openpilot directory adjusted."
                    else
                        log_error "Error while adjusting permissions for openpilot directory."
                    fi

                    # Ensure fork_swap.sh is present in the cloned fork
                    ensure_fork_swap_script

                    chmod +x $OPENPILOT_DIR/scripts/fork_swap.sh
                    if [[ $? -eq 0 ]]; then
                        log_info "Permissions for fork_swap.sh adjusted."
                    else
                        log_error "Error while adjusting permissions for fork_swap.sh."
                    fi

                    echo "Switched to $fork. Rebooting..."
                    sudo reboot
                else
                    echo "Exiting without making changes."
                    exit 0
                fi
            else
                echo "Invalid choice. Please type the name of one of the available forks or 'Clone a new fork'."
            fi
            ;;
    esac
done
