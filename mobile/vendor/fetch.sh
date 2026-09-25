#!/bin/sh
# Test-only dependencies for mobile/check-mobile.mjs (not shipped, not committed: ~18 MB).
# supabase-js is the exact version index.html pins; its dist/umd/supabase.js matches the SRI hash there.
set -e; cd "$(dirname "$0")"
for p in @supabase/supabase-js@2.112.4 @fontsource/inter@5.3.0 @fontsource/spectral@5.3.0 @fontsource/newsreader@5.3.0; do npm pack "$p" >/dev/null; done
mkdir -p supabase-supabase-js-2.112.4 fontsource-inter-5.3.0 fontsource-spectral-5.3.0 nr
tar -xzf supabase-supabase-js-2.112.4.tgz -C supabase-supabase-js-2.112.4
tar -xzf fontsource-inter-5.3.0.tgz -C fontsource-inter-5.3.0
tar -xzf fontsource-spectral-5.3.0.tgz -C fontsource-spectral-5.3.0
tar -xzf fontsource-newsreader-5.3.0.tgz -C nr
echo "vendor ready"
