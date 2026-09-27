%post --erroronfail --nochroot --log=/tmp/privos-secureboot-enroll-key.log
# Schlüssel der signierten NVIDIA-Treiber für Secure Boot vormerken.
# Beim ersten Neustart: "Enroll MOK" -> "Continue" -> "Yes" -> Passwort: privos
set -euo pipefail
readonly ENROLLMENT_PASSWORD="privos"
readonly SECUREBOOT_KEY="/etc/pki/akmods/certs/akmods-ublue.der"

if [[ ! -d /sys/firmware/efi ]]; then
    echo "Kein UEFI – Schlüssel wird nicht registriert."
    exit 0
fi
if [[ ! -f "${SECUREBOOT_KEY}" ]]; then
    echo "Schlüssel fehlt: ${SECUREBOOT_KEY}"
    exit 0
fi
mokutil --timeout -1 || :
echo -e "${ENROLLMENT_PASSWORD}\n${ENROLLMENT_PASSWORD}" | mokutil --import "${SECUREBOOT_KEY}" || :
%end
