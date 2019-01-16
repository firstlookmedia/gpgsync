# Example Keylist

If you'd like to test out GPG Sync before you create your own authority
key and fingerprints file, you can use this one. In GPG Sync, create a
new endpoint with the following settings:

* Authority Key Fingerprint: `4CA5857F960C8A78D82C11F36D00387A7A0206E2`
* Keylist Address: `https://raw.githubusercontent.com/firstlookmedia/gpgsync/develop/example-keylist/keylist.json`

After syncing for the first time, your GPG keyring should contain a few
new keys.
