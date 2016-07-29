# Fingerprints File

If you'd like to test out GPG Sync before you create your own authority key and fingerprints file, you can use this one. In GPG Sync, create a new endpoint with the following settings:

* Signing key fingerprint: `A642 37D7 ADD1 7B2A 51D8  B8E8 70FE 91BC 9AD2 58AF`
* Signed fingerprints URL: `https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt.asc`

After syncing for the first time, your GPG keyring should contain a few new keys.
