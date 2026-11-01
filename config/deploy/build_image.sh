#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
docker build -f config/deploy/Dockerfile -t mois-d-zois .
