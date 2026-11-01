Set-Location (Join-Path $PSScriptRoot "../..")
docker build -f config/deploy/Dockerfile -t mois-d-zois .
