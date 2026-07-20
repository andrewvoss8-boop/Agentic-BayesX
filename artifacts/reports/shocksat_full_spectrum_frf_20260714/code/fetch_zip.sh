#!/bin/bash
# fetch_zip.sh <zipname> <expected_bytes> — resumable, retrying download from mediaex (card §4).
# One zip at a time; checks free disk (>1.5 GB) before starting; retries partial transfers up to 40 times.
set -u
WS="$(cd "$(dirname "$0")/.." && pwd)"
NAME="$1"; WANT="$2"
URL="https://mediaex-server.larc.nasa.gov/shocksat/Test_Data_Impact/${NAME}"
OUT="${WS}/data/zips/${NAME}"
mkdir -p "${WS}/data/zips"
FREE_KB=$(df -k "${WS}" | tail -1 | awk '{print $4}')
if [ "${FREE_KB}" -lt 1572864 ]; then
  echo "ABORT: free disk ${FREE_KB} KB < 1.5 GB threshold" >&2
  exit 3
fi
for i in $(seq 1 40); do
  SZ=$(stat -f %z "${OUT}" 2>/dev/null || echo 0)
  if [ "${SZ}" -ge "${WANT}" ]; then break; fi
  echo "attempt ${i}: have ${SZ}/${WANT}"
  curl -sSL -C - --retry 5 --retry-delay 5 --max-time 3600 -o "${OUT}" "${URL}"
  sleep 3
done
SZ=$(stat -f %z "${OUT}" 2>/dev/null || echo 0)
if [ "${SZ}" -ne "${WANT}" ]; then
  echo "FAILED: ${NAME} has ${SZ}, expected ${WANT}" >&2
  exit 2
fi
shasum -a 256 "${OUT}"
echo "DONE ${NAME}"
