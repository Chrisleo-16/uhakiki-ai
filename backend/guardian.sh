#!/bin/bash
# =============================================================
#  guardian.sh
#  Self-monitoring security system with Human-in-the-Loop (HITL)
#
#  - Continuously monitors your system for vulnerabilities
#  - Detects changes in files, services, ports, users
#  - Proposes fixes but NEVER applies them without your password
#  - Logs everything to ~/guardian_logs/
#
#  Usage:
#    chmod +x guardian.sh
#    sudo ./guardian.sh             # full interactive mode
#    sudo ./guardian.sh --monitor   # background monitoring only
#    sudo ./guardian.sh --report    # just generate a report
# =============================================================

# ── Configuration ─────────────────────────────────────────────
GUARDIAN_DIR="$HOME/guardian"
LOG_DIR="$GUARDIAN_DIR/logs"
SNAPSHOT_DIR="$GUARDIAN_DIR/snapshots"
FIXES_DIR="$GUARDIAN_DIR/approved_fixes"
PENDING_DIR="$GUARDIAN_DIR/pending_fixes"
WATCH_INTERVAL=30          # seconds between monitoring cycles
MAX_AUTO_RETRY=3           # max times to retry a failed fix

mkdir -p "$LOG_DIR" "$SNAPSHOT_DIR" "$FIXES_DIR" "$PENDING_DIR"

DATE=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="$LOG_DIR/guardian_$DATE.log"
ALERT_LOG="$LOG_DIR/alerts.log"
CHANGE_LOG="$LOG_DIR/changes.log"

# ── Colours ───────────────────────────────────────────────────
G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"
B="\033[1m";  M="\033[95m"; X="\033[0m"

ok()      { local m="[OK]    $*";    echo -e "${G}  ✅ $*${X}";         echo "$m" >> "$MAIN_LOG"; }
bad()     { local m="[VULN]  $*";    echo -e "${R}  🚨 VULN: $*${X}";   echo "$m" >> "$MAIN_LOG"; echo "$m" >> "$ALERT_LOG"; }
warn()    { local m="[WARN]  $*";    echo -e "${Y}  ⚠️  $*${X}";         echo "$m" >> "$MAIN_LOG"; }
info()    { local m="[INFO]  $*";    echo -e "${C}  ➜  $*${X}";          echo "$m" >> "$MAIN_LOG"; }
change()  { local m="[CHANGE] $*";   echo -e "${M}  🔄 CHANGE: $*${X}";  echo "$m" >> "$CHANGE_LOG"; echo "$m" >> "$MAIN_LOG"; }
hdr()     {
  echo -e "\n${B}${C}══════════════════════════════════════════"
  echo -e "  $*"
  echo -e "══════════════════════════════════════════${X}"
  echo -e "\n=== $* ===" >> "$MAIN_LOG"
}


# ══════════════════════════════════════════════════════════════
#  HUMAN-IN-THE-LOOP ENGINE
#  Every fix goes through here — nothing runs without approval
# ══════════════════════════════════════════════════════════════

# Tracks approved fixes this session so you aren't re-asked
declare -A SESSION_APPROVED

request_approval() {
  local fix_id="$1"        # unique ID for this fix
  local title="$2"         # short title
  local description="$3"   # what the vulnerability is
  local fix_command="$4"   # exact command that will run
  local risk_level="$5"    # LOW / MEDIUM / HIGH
  local rollback_cmd="$6"  # how to undo (shown to user)

  # Skip if already approved this session
  if [ "${SESSION_APPROVED[$fix_id]}" = "yes" ]; then
    return 0
  fi

  # Save to pending fixes log
  local pending_file="$PENDING_DIR/${fix_id}.pending"
  cat > "$pending_file" << EOF
FIX_ID:       $fix_id
TITLE:        $title
RISK:         $risk_level
DESCRIPTION:  $description
COMMAND:      $fix_command
ROLLBACK:     $rollback_cmd
REQUESTED_AT: $(date)
STATUS:       PENDING
EOF

  echo ""
  echo -e "${R}${B}╔══════════════════════════════════════════════════╗"
  echo -e "║           🔐 APPROVAL REQUIRED                   ║"
  echo -e "╚══════════════════════════════════════════════════╝${X}"
  echo ""
  echo -e "  ${B}Fix ID    :${X} $fix_id"
  echo -e "  ${B}Title     :${X} $title"
  echo -e "  ${B}Risk Level:${X} $(risk_colour $risk_level)"
  echo ""
  echo -e "  ${Y}Vulnerability:${X}"
  echo "  $description" | fold -s -w 60 | sed 's/^/    /'
  echo ""
  echo -e "  ${C}Proposed fix command:${X}"
  echo -e "  ${B}  $fix_command${X}"
  echo ""
  echo -e "  ${C}How to undo if needed:${X}"
  echo "    $rollback_cmd"
  echo ""
  echo -e "${Y}  Options:${X}"
  echo "    [Y] Yes — enter your password to approve and apply"
  echo "    [N] No  — skip this fix for now (logged)"
  echo "    [V] View — show more details"
  echo "    [D] Defer — remind me next scan"
  echo ""
  read -rp "  Your choice [Y/N/V/D]: " choice

  case "${choice^^}" in
    Y)
      # Require sudo password — acts as explicit human confirmation
      echo ""
      echo -e "  ${C}Enter your sudo password to authorise this change:${X}"
      if sudo -k && sudo -v 2>/dev/null; then
        SESSION_APPROVED[$fix_id]="yes"
        sed -i "s/STATUS:       PENDING/STATUS:       APPROVED/" "$pending_file"
        mv "$pending_file" "$FIXES_DIR/${fix_id}_approved.fix"

        echo ""
        info "Applying fix: $title"
        echo -e "  ${G}Running: $fix_command${X}"
        echo ""

        # Run the fix and capture output + exit code
        FIX_OUTPUT=$(eval "$fix_command" 2>&1)
        FIX_EXIT=$?

        if [ $FIX_EXIT -eq 0 ]; then
          ok "Fix applied successfully: $title"
          echo "FIX_RESULT: SUCCESS" >> "$FIXES_DIR/${fix_id}_approved.fix"
          echo "OUTPUT: $FIX_OUTPUT"  >> "$FIXES_DIR/${fix_id}_approved.fix"
          log_fix_applied "$fix_id" "$title" "$fix_command" "SUCCESS"
          return 0
        else
          bad "Fix failed (exit $FIX_EXIT): $FIX_OUTPUT"
          echo "FIX_RESULT: FAILED — $FIX_OUTPUT" >> "$FIXES_DIR/${fix_id}_approved.fix"
          log_fix_applied "$fix_id" "$title" "$fix_command" "FAILED: $FIX_OUTPUT"
          return 1
        fi
      else
        warn "Password incorrect or cancelled — fix NOT applied"
        sed -i "s/STATUS:       PENDING/STATUS:       AUTH_FAILED/" "$pending_file"
        return 1
      fi
      ;;

    N)
      warn "Fix skipped by user: $title"
      sed -i "s/STATUS:       PENDING/STATUS:       SKIPPED/" "$pending_file"
      log_fix_skipped "$fix_id" "$title"
      return 1
      ;;

    V)
      echo ""
      echo -e "${C}=== Detailed Info ===${X}"
      echo "  Vulnerability: $description"
      echo "  Command to run: $fix_command"
      echo "  Rollback: $rollback_cmd"
      echo "  Risk: $risk_level"
      echo ""
      # Re-ask after viewing
      request_approval "$fix_id" "$title" "$description" "$fix_command" "$risk_level" "$rollback_cmd"
      ;;

    D)
      warn "Fix deferred: $title — will ask again next scan"
      sed -i "s/STATUS:       PENDING/STATUS:       DEFERRED/" "$pending_file"
      return 1
      ;;

    *)
      warn "Invalid choice — fix skipped"
      return 1
      ;;
  esac
}

risk_colour() {
  case "$1" in
    HIGH)   echo -e "${R}${B}HIGH${X}" ;;
    MEDIUM) echo -e "${Y}MEDIUM${X}" ;;
    LOW)    echo -e "${G}LOW${X}" ;;
    *)      echo "$1" ;;
  esac
}

log_fix_applied() {
  echo "[$(date)] APPLIED  | $1 | $2 | CMD: $3 | RESULT: $4" >> "$LOG_DIR/fix_history.log"
}

log_fix_skipped() {
  echo "[$(date)] SKIPPED  | $1 | $2" >> "$LOG_DIR/fix_history.log"
}


# ══════════════════════════════════════════════════════════════
#  SNAPSHOT ENGINE
#  Takes baseline snapshots so changes can be detected
# ══════════════════════════════════════════════════════════════

take_snapshot() {
  local label="$1"
  local snap="$SNAPSHOT_DIR/$label"
  mkdir -p "$snap"

  # Ports
  ss -tulnp > "$snap/ports.txt" 2>/dev/null

  # Users
  cat /etc/passwd > "$snap/users.txt" 2>/dev/null

  # Services
  systemctl list-units --type=service --state=running --no-pager > "$snap/services.txt" 2>/dev/null

  # SUID files
  find / -perm -4000 -type f 2>/dev/null | sort > "$snap/suid.txt"

  # Cron jobs
  crontab -l 2>/dev/null > "$snap/crontab.txt"
  cat /etc/crontab 2>/dev/null >> "$snap/crontab.txt"

  # SSH config hash
  md5sum /etc/ssh/sshd_config 2>/dev/null > "$snap/sshd_config.md5"

  # Sudo rules
  sudo cat /etc/sudoers 2>/dev/null > "$snap/sudoers.txt"

  # Firewall rules
  sudo iptables -L -n 2>/dev/null > "$snap/iptables.txt"

  # Installed packages
  dpkg -l 2>/dev/null > "$snap/packages.txt"

  # Critical file hashes
  for f in /etc/passwd /etc/shadow /etc/sudoers /etc/ssh/sshd_config \
            /etc/hosts /etc/crontab /etc/fstab; do
    [ -f "$f" ] && md5sum "$f" 2>/dev/null
  done > "$snap/critical_files.md5"

  info "Snapshot saved: $label"
}

compare_snapshots() {
  local old="$SNAPSHOT_DIR/baseline"
  local new="$SNAPSHOT_DIR/current"

  [ ! -d "$old" ] && warn "No baseline snapshot — run with --baseline first" && return

  hdr "Change Detection"

  # ── New ports ─────────────────────────────────────────────
  NEW_PORTS=$(comm -13 \
    <(awk '{print $5}' "$old/ports.txt" 2>/dev/null | sort) \
    <(awk '{print $5}' "$new/ports.txt" 2>/dev/null | sort))
  if [ -n "$NEW_PORTS" ]; then
    change "New ports opened since baseline: $NEW_PORTS"
    bad "Unexpected open ports detected — possible backdoor or new service"
  else
    ok "No new ports opened"
  fi

  # ── New users ─────────────────────────────────────────────
  NEW_USERS=$(comm -13 \
    <(awk -F: '{print $1}' "$old/users.txt" 2>/dev/null | sort) \
    <(awk -F: '{print $1}' "$new/users.txt" 2>/dev/null | sort))
  if [ -n "$NEW_USERS" ]; then
    change "New user accounts created: $NEW_USERS"
    bad "Unexpected new users — possible account creation attack"
    request_approval \
      "remove_user_$NEW_USERS" \
      "Remove unexpected user: $NEW_USERS" \
      "A new user '$NEW_USERS' appeared since the last baseline snapshot. This could indicate an attacker created a backdoor account." \
      "sudo userdel -r $NEW_USERS" \
      "HIGH" \
      "sudo useradd $NEW_USERS  (recreate if you added them yourself)"
  else
    ok "No new user accounts"
  fi

  # ── New SUID files ────────────────────────────────────────
  NEW_SUID=$(comm -13 \
    <(sort "$old/suid.txt" 2>/dev/null) \
    <(sort "$new/suid.txt" 2>/dev/null))
  if [ -n "$NEW_SUID" ]; then
    change "New SUID files appeared: $NEW_SUID"
    bad "New SUID binary detected — could be privilege escalation vector"
    for suid_file in $NEW_SUID; do
      request_approval \
        "remove_suid_$(basename $suid_file)" \
        "Remove SUID bit from: $suid_file" \
        "The file '$suid_file' gained the SUID bit since your baseline. SUID files run as root — unexpected ones are dangerous." \
        "sudo chmod u-s $suid_file" \
        "HIGH" \
        "sudo chmod u+s $suid_file  (restore if intentional)"
    done
  else
    ok "No new SUID files"
  fi

  # ── Critical file changes ─────────────────────────────────
  OLD_MD5="$old/critical_files.md5"
  NEW_MD5="$new/critical_files.md5"
  if [ -f "$OLD_MD5" ] && [ -f "$NEW_MD5" ]; then
    CHANGED_FILES=$(diff "$OLD_MD5" "$NEW_MD5" | grep "^>" | awk '{print $2}')
    if [ -n "$CHANGED_FILES" ]; then
      for cf in $CHANGED_FILES; do
        change "Critical file modified: $cf"
        bad "Unexpected change in $cf — review immediately"
        # Show the diff
        echo ""
        echo -e "  ${Y}Diff for $cf:${X}"
        diff \
          <(grep "$cf" "$OLD_MD5") \
          <(grep "$cf" "$NEW_MD5") || true
      done
    else
      ok "No critical files modified"
    fi
  fi

  # ── New cron jobs ─────────────────────────────────────────
  NEW_CRON=$(diff "$old/crontab.txt" "$new/crontab.txt" 2>/dev/null | grep "^>" | grep -v "^#")
  if [ -n "$NEW_CRON" ]; then
    change "New cron jobs detected: $NEW_CRON"
    bad "Unexpected cron entries — possible persistence mechanism"
  else
    ok "No new cron jobs"
  fi

  # ── New services ──────────────────────────────────────────
  NEW_SERVICES=$(comm -13 \
    <(awk '{print $1}' "$old/services.txt" 2>/dev/null | sort) \
    <(awk '{print $1}' "$new/services.txt" 2>/dev/null | sort))
  if [ -n "$NEW_SERVICES" ]; then
    change "New services started: $NEW_SERVICES"
    warn "Review these new services: $NEW_SERVICES"
  else
    ok "No new services started"
  fi
}


# ══════════════════════════════════════════════════════════════
#  VULNERABILITY SCANNER
#  Scans and immediately proposes fixes with HITL approval
# ══════════════════════════════════════════════════════════════

scan_ssh() {
  hdr "SSH Security Scan"

  if ! ss -tlnp | grep -q ':22'; then
    ok "SSH is not running"; return
  fi

  # Root login
  if grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null; then
    bad "Root SSH login is ENABLED"
    request_approval \
      "ssh_disable_root_login" \
      "Disable root SSH login" \
      "PermitRootLogin is set to 'yes' in sshd_config. This allows attackers to brute-force directly into the root account over SSH." \
      "sudo sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config && sudo systemctl restart ssh" \
      "HIGH" \
      "sudo sed -i 's/^PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config && sudo systemctl restart ssh"
  else
    ok "Root SSH login is disabled"
  fi

  # Password authentication
  if grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config 2>/dev/null; then
    bad "SSH password authentication is ENABLED"
    request_approval \
      "ssh_disable_password_auth" \
      "Disable SSH password authentication (key-only)" \
      "PasswordAuthentication is enabled. Password-based SSH is vulnerable to brute-force attacks. Key-based auth is much stronger." \
      "sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && sudo systemctl restart ssh" \
      "MEDIUM" \
      "sudo sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && sudo systemctl restart ssh"
  else
    ok "SSH password authentication is disabled"
  fi

  # SSH port 22 (default)
  if grep -q "^#Port 22\|^Port 22" /etc/ssh/sshd_config 2>/dev/null || \
     ! grep -q "^Port" /etc/ssh/sshd_config 2>/dev/null; then
    warn "SSH is running on default port 22 — easy to find via scanners"
    request_approval \
      "ssh_change_port" \
      "Move SSH to a non-standard port (e.g. 2222)" \
      "Running SSH on port 22 makes it an easy target for automated scanners and bots. Moving it reduces noise and attack surface." \
      "sudo sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config && sudo systemctl restart ssh && sudo ufw allow 2222/tcp" \
      "LOW" \
      "sudo sed -i 's/^Port 2222/Port 22/' /etc/ssh/sshd_config && sudo systemctl restart ssh"
  fi

  # Empty passwords
  if grep -q "^PermitEmptyPasswords yes" /etc/ssh/sshd_config 2>/dev/null; then
    bad "SSH PERMITS EMPTY PASSWORDS"
    request_approval \
      "ssh_no_empty_passwords" \
      "Disable empty password SSH login" \
      "PermitEmptyPasswords is set to yes. Any account with no password can log in via SSH — critical vulnerability." \
      "sudo sed -i 's/^PermitEmptyPasswords yes/PermitEmptyPasswords no/' /etc/ssh/sshd_config && sudo systemctl restart ssh" \
      "HIGH" \
      "sudo sed -i 's/^PermitEmptyPasswords no/PermitEmptyPasswords yes/' /etc/ssh/sshd_config && sudo systemctl restart ssh"
  fi

  # MaxAuthTries
  MAX_AUTH=$(grep "^MaxAuthTries" /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}')
  if [ -z "$MAX_AUTH" ] || [ "$MAX_AUTH" -gt 4 ]; then
    warn "MaxAuthTries not set or too high ($MAX_AUTH) — allows brute force"
    request_approval \
      "ssh_max_auth_tries" \
      "Set MaxAuthTries to 3" \
      "MaxAuthTries controls how many password attempts are allowed before disconnecting. High values allow brute-force attacks." \
      "echo 'MaxAuthTries 3' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl restart ssh" \
      "MEDIUM" \
      "sudo sed -i '/^MaxAuthTries 3/d' /etc/ssh/sshd_config && sudo systemctl restart ssh"
  else
    ok "MaxAuthTries = $MAX_AUTH"
  fi
}

scan_firewall() {
  hdr "Firewall Scan"

  UFW_STATUS=$(sudo ufw status 2>/dev/null | head -1)
  if echo "$UFW_STATUS" | grep -q "inactive\|Status: inactive"; then
    bad "Firewall (UFW) is DISABLED"
    request_approval \
      "enable_ufw_firewall" \
      "Enable UFW firewall with safe defaults" \
      "The UFW firewall is completely disabled. All ports are exposed with no filtering. Enabling UFW blocks everything except what you explicitly allow." \
      "sudo ufw default deny incoming && sudo ufw default allow outgoing && sudo ufw allow ssh && sudo ufw --force enable" \
      "HIGH" \
      "sudo ufw disable"
  else
    ok "Firewall is active"
    sudo ufw status verbose 2>/dev/null | grep -v "^$" | head -20
  fi
}

scan_users() {
  hdr "User Account Scan"

  # UID 0 accounts other than root
  UID0=$(awk -F: '($3 == 0 && $1 != "root") {print $1}' /etc/passwd)
  if [ -n "$UID0" ]; then
    bad "Non-root account with UID 0: $UID0"
    request_approval \
      "fix_uid0_$UID0" \
      "Fix UID-0 account: $UID0" \
      "The account '$UID0' has UID 0 which gives it full root privileges. Only 'root' should have UID 0." \
      "sudo usermod -u 1001 $UID0" \
      "HIGH" \
      "sudo usermod -u 0 $UID0  (restore — only if intentional)"
  else
    ok "No unexpected UID-0 accounts"
  fi

  # Empty passwords
  EMPTY_PASS=$(sudo awk -F: '($2 == "" || $2 == "!!" ) {print $1}' /etc/shadow 2>/dev/null)
  if [ -n "$EMPTY_PASS" ]; then
    bad "Accounts with empty/locked passwords: $EMPTY_PASS"
    for acct in $EMPTY_PASS; do
      request_approval \
        "lock_empty_account_$acct" \
        "Lock account with empty password: $acct" \
        "The account '$acct' has no password set. Anyone can switch to it without a password." \
        "sudo passwd -l $acct" \
        "HIGH" \
        "sudo passwd -u $acct  (unlock)"
    done
  else
    ok "No accounts with empty passwords"
  fi
}

scan_suid() {
  hdr "SUID Binary Scan"

  DANGEROUS=(nmap vim nano bash python python3 perl ruby find wget curl \
    awk sed tar zip gzip more less man cp mv tee env strace pkexec)

  for bin in "${DANGEROUS[@]}"; do
    SUID_PATH=$(find / -name "$bin" -perm -4000 2>/dev/null | head -1)
    if [ -n "$SUID_PATH" ]; then
      bad "Dangerous SUID binary: $SUID_PATH"
      request_approval \
        "remove_suid_$bin" \
        "Remove SUID bit from $bin" \
        "The binary '$SUID_PATH' has the SUID bit set. This means any user can run it AS ROOT. '$bin' is on the GTFOBins list — it can be exploited to get a root shell." \
        "sudo chmod u-s $SUID_PATH" \
        "HIGH" \
        "sudo chmod u+s $SUID_PATH  (restore)"
    fi
  done
}

scan_updates() {
  hdr "Pending Security Updates"

  UPDATES=$(apt list --upgradable 2>/dev/null | grep -c "upgradable" || echo 0)
  if [ "$UPDATES" -gt 0 ]; then
    warn "$UPDATES packages have updates available"
    apt list --upgradable 2>/dev/null | grep -v "Listing" | head -20

    SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -i "security" | wc -l)
    if [ "$SECURITY_UPDATES" -gt 0 ]; then
      bad "$SECURITY_UPDATES SECURITY updates pending"
      request_approval \
        "apply_security_updates" \
        "Apply $SECURITY_UPDATES security updates" \
        "$SECURITY_UPDATES packages have security patches available. Unpatched software is the most common attack vector." \
        "sudo apt update && sudo apt upgrade -y" \
        "MEDIUM" \
        "Use 'sudo apt-get install <package>=<old-version>' to downgrade specific packages if needed"
    fi
  else
    ok "System is up to date"
  fi
}

scan_open_ports() {
  hdr "Open Port Scan"

  info "Scanning all ports..."
  OPEN_PORTS=$(sudo nmap -p- --open -T4 127.0.0.1 2>/dev/null | \
    grep "^[0-9]" | awk '{print $1}')

  for port_proto in $OPEN_PORTS; do
    port=$(echo "$port_proto" | cut -d/ -f1)
    case $port in
      23)
        bad "Telnet (port 23) is open — transmits data in PLAINTEXT"
        request_approval \
          "disable_telnet" \
          "Disable Telnet service" \
          "Telnet sends everything including passwords in plain text. It should never be used. Replace with SSH." \
          "sudo systemctl stop telnet && sudo systemctl disable telnet && sudo ufw deny 23" \
          "HIGH" \
          "sudo systemctl enable telnet && sudo systemctl start telnet"
        ;;
      21)
        bad "FTP (port 21) is open — check if anonymous login is enabled"
        ;;
      3389)
        warn "RDP (port 3389) is exposed — ensure strong password and consider VPN"
        ;;
      6379)
        bad "Redis (port 6379) is exposed — often unauthenticated by default"
        request_approval \
          "block_redis_external" \
          "Block Redis port from external access" \
          "Redis on port 6379 is accessible. Redis often has no authentication by default and can be exploited to read/write data or gain RCE." \
          "sudo ufw deny 6379 && sudo ufw allow from 127.0.0.1 to any port 6379" \
          "HIGH" \
          "sudo ufw delete deny 6379"
        ;;
      27017)
        bad "MongoDB (port 27017) is exposed — often unauthenticated by default"
        request_approval \
          "block_mongo_external" \
          "Block MongoDB from external access" \
          "MongoDB on 27017 is externally accessible. Default installs often have no authentication — this is a critical data exposure risk." \
          "sudo ufw deny 27017 && sudo ufw allow from 127.0.0.1 to any port 27017" \
          "HIGH" \
          "sudo ufw delete deny 27017"
        ;;
    esac
  done
}

scan_world_writable() {
  hdr "World-Writable Files"

  WW_FILES=$(find /etc /usr /bin /sbin -xdev -type f -perm -0002 2>/dev/null)
  if [ -n "$WW_FILES" ]; then
    bad "World-writable files in system directories:"
    echo "$WW_FILES" | head -10
    for f in $WW_FILES; do
      request_approval \
        "fix_worldwrite_$(echo $f | tr '/' '_')" \
        "Fix world-writable: $f" \
        "The file '$f' is writable by any user. In a system directory this could allow privilege escalation or code injection." \
        "sudo chmod o-w $f" \
        "MEDIUM" \
        "sudo chmod o+w $f  (restore)"
    done
  else
    ok "No world-writable files in system directories"
  fi
}


# ══════════════════════════════════════════════════════════════
#  CONTINUOUS MONITOR MODE
# ══════════════════════════════════════════════════════════════

monitor_loop() {
  hdr "Guardian Monitor — watching every ${WATCH_INTERVAL}s (Ctrl+C to stop)"
  info "Taking initial baseline snapshot..."
  take_snapshot "baseline"

  CYCLE=0
  while true; do
    CYCLE=$((CYCLE + 1))
    echo ""
    echo -e "${B}${C}[$(date '+%H:%M:%S')] Scan cycle #$CYCLE${X}"

    take_snapshot "current"
    compare_snapshots

    # Run quick vulnerability checks
    scan_ssh
    scan_firewall
    scan_users
    scan_open_ports

    echo ""
    info "Next scan in ${WATCH_INTERVAL}s — press Ctrl+C to stop monitoring"
    sleep "$WATCH_INTERVAL"
  done
}


# ══════════════════════════════════════════════════════════════
#  FULL REPORT
# ══════════════════════════════════════════════════════════════

full_report() {
  hdr "Guardian Full Security Report"
  echo "Generated: $(date)" | tee -a "$MAIN_LOG"
  echo "System: $(uname -a)" | tee -a "$MAIN_LOG"

  take_snapshot "current"
  compare_snapshots
  scan_ssh
  scan_firewall
  scan_users
  scan_suid
  scan_updates
  scan_open_ports
  scan_world_writable

  # Summary
  hdr "Report Summary"
  VULNS=$(grep -c "\[VULN\]" "$MAIN_LOG" 2>/dev/null || echo 0)
  CHANGES=$(grep -c "\[CHANGE\]" "$CHANGE_LOG" 2>/dev/null || echo 0)
  FIXES_APPLIED=$(grep -c "APPLIED" "$LOG_DIR/fix_history.log" 2>/dev/null || echo 0)
  FIXES_SKIPPED=$(grep -c "SKIPPED" "$LOG_DIR/fix_history.log" 2>/dev/null || echo 0)

  echo ""
  echo -e "  ${R}Vulnerabilities found : $VULNS${X}"
  echo -e "  ${M}Changes detected      : $CHANGES${X}"
  echo -e "  ${G}Fixes applied         : $FIXES_APPLIED${X}"
  echo -e "  ${Y}Fixes skipped         : $FIXES_SKIPPED${X}"
  echo ""
  echo -e "  ${B}Full log   :${X} $MAIN_LOG"
  echo -e "  ${B}Alerts     :${X} $ALERT_LOG"
  echo -e "  ${B}Changes    :${X} $CHANGE_LOG"
  echo -e "  ${B}Fix history:${X} $LOG_DIR/fix_history.log"
  echo ""

  if [ "$VULNS" -gt 0 ]; then
    echo -e "${R}  Vulnerabilities:${X}"
    grep "\[VULN\]" "$MAIN_LOG" | sed 's/.*\[VULN\]/  🚨/'
  fi

  if [ "$CHANGES" -gt 0 ]; then
    echo -e "${M}  Changes detected:${X}"
    grep "\[CHANGE\]" "$CHANGE_LOG" | sed 's/.*\[CHANGE\]/  🔄/'
  fi
}


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════

echo -e "${B}${C}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║   🛡️  Guardian — Security Monitor v1.0    ║"
echo "  ║   Human-in-the-Loop Protection System    ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${X}"
echo -e "  ${C}Logs:${X} $GUARDIAN_DIR"
echo ""

case "$1" in
  --monitor)
    monitor_loop
    ;;
  --report)
    full_report
    ;;
  --baseline)
    take_snapshot "baseline"
    ok "Baseline snapshot saved — run again to detect changes"
    ;;
  --changes)
    take_snapshot "current"
    compare_snapshots
    ;;
  --history)
    hdr "Fix History"
    cat "$LOG_DIR/fix_history.log" 2>/dev/null || info "No fix history yet"
    ;;
  --pending)
    hdr "Pending Fixes"
    ls "$PENDING_DIR"/*.pending 2>/dev/null | while read f; do
      echo ""; cat "$f"; echo "─────────────────"
    done || info "No pending fixes"
    ;;
  *)
    # Default: full interactive scan + HITL fixes
    full_report
    echo ""
    echo -e "${C}Other modes:${X}"
    echo "  sudo ./guardian.sh --monitor    # watch continuously every ${WATCH_INTERVAL}s"
    echo "  sudo ./guardian.sh --baseline   # save a clean snapshot"
    echo "  sudo ./guardian.sh --changes    # detect changes since baseline"
    echo "  sudo ./guardian.sh --history    # show all approved/skipped fixes"
    echo "  sudo ./guardian.sh --pending    # show pending fix requests"
    echo ""
    ;;
esac