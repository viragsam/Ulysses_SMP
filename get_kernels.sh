#!/usr/bin/env bash
# Downloads the NAIF SPICE kernels listed in smp.tm into ./kernels/
# Usage: ./get_kernels.sh   (run from the project root)
set -e

B=https://naif.jpl.nasa.gov/pub/naif/generic_kernels
mkdir -p kernels/{lsk,spk,pck,fk}

wget -nc -P kernels/lsk "$B/lsk/naif0012.tls"
wget -nc -P kernels/spk "$B/spk/planets/de440s.bsp"
wget -nc -P kernels/pck "$B/pck/pck00011.tpc"
wget -nc -P kernels/pck "$B/pck/moon_pa_de440_200625.bpc"
wget -nc -P kernels/fk  "$B/fk/satellites/moon_de440_250416.tf"

echo "Kernels downloaded to ./kernels/"
