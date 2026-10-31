#!/usr/bin/env python3
"""Connect contacts (2026-10-30), the iPhone side: @capacitor-community/contacts 8.0.0 (the only
Capacitor-8 contacts plugin on npm; peerDependencies @capacitor/core >=8.0.0, SPM Package.swift,
iOS 15+, reports iOS 18 "limited" access). The page finds it as Capacitor.Plugins.Contacts.

Run from the repo root:  python3 ios-contacts-wiring-2026-10-30.py ios-app
It edits the three tracked files exactly as `npm install` + `npx cap sync ios` would leave them, plus
the one thing sync can't write (the permission text):
  1. ios-app/package.json                  "@capacitor-community/contacts": "8.0.0"
  2. ios-app/ios/App/CapApp-SPM/Package.swift  .package(name: "CapacitorCommunityContacts", path: …node_modules/@capacitor-community/contacts)
                                              .product(name: "CapacitorCommunityContacts", package: "CapacitorCommunityContacts")
  3. ios-app/ios/App/App/Info.plist         NSContactsUsageDescription
Then, on the Mac:
  cd ios-app && npm install          # fetches the plugin, updates package-lock.json
  npm run sync                       # copies the web app; regenerates ios/App/App/capacitor.config.json
                                     # (gitignored) — its packageClassList must now include "ContactsPlugin"
  grep ContactsPlugin ios/App/App/capacitor.config.json   # check
  npm run open → Product › Clean Build Folder → Run on the iPhone.
Device check: Friends › Contacts › Connect contacts → iOS asks once (on iOS 18 it offers "Select contacts"
/ "Allow full access"; both work) → results. Settings › TermChamp › Contacts off → the sheet says how to
turn it back on. Before App Store submission: App Privacy label gets "Contacts" (App Functionality,
not used for tracking) and the Privacy Policy says contacts are hashed on the phone and not stored."""
import sys, json, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'ios-app')

# 1. package.json (keeps the file's 2-space layout and key order; dependencies stay sorted)
pj = root / 'package.json'; d = json.loads(pj.read_text())
assert '@capacitor-community/contacts' not in d['dependencies'], 'already wired'
d['dependencies']['@capacitor-community/contacts'] = '8.0.0'
d['dependencies'] = dict(sorted(d['dependencies'].items()))
pj.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')

def edit(path, pairs):
    s = path.read_text()
    for a, b in pairs:
        n = s.count(a); assert n == 1, (path.name, a[:60], n); s = s.replace(a, b)
    path.write_text(s)

# 2. Package.swift — the same lines `npx cap sync ios` generates (alphabetical: community before keyboard)
edit(root / 'ios/App/CapApp-SPM/Package.swift', [
    ('''        .package(url: "https://github.com/ionic-team/capacitor-swift-pm.git", exact: "8.5.2"),
''', '''        .package(url: "https://github.com/ionic-team/capacitor-swift-pm.git", exact: "8.5.2"),
        .package(name: "CapacitorCommunityContacts", path: "../../../node_modules/@capacitor-community/contacts"),
'''),
    ('''                .product(name: "Cordova", package: "capacitor-swift-pm"),
''', '''                .product(name: "Cordova", package: "capacitor-swift-pm"),
                .product(name: "CapacitorCommunityContacts", package: "CapacitorCommunityContacts"),
''')])

# 3. Info.plist — iOS shows this under "TermChamp Would Like to Access Your Contacts"
edit(root / 'ios/App/App/Info.plist', [
    ('''	<key>NSCameraUsageDescription</key>''', '''	<key>NSContactsUsageDescription</key>
	<string>TermChamp shows you which of your contacts are already on TermChamp.</string>
	<key>NSCameraUsageDescription</key>''')])
print(root, 'contacts plugin wired: package.json, Package.swift, Info.plist — now npm install && npm run sync on the Mac')
