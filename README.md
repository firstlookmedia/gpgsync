# PGP Sync

![PGP Sync](/logo/logo.png)

PGP Sync is designed to let users always have up-to-date PGP public keys for other members of their organization.

If you're part of an organization that uses PGP internally you might notice that it doesn't scale well. New people join and create new keys and existing people revoke their old keys and transition to new ones. It quickly becomes unwieldy to ensure that everyone has a copy of everyone else's current key, and that old revoked keys get refreshed to prevent users from accidentally using them.

PGP Sync solves this problem by offloading the complexity of PGP to a single trusted person in your organization (referred to here as the "techie"). As a member of an organization, you install PGP Sync on your computer, configure it with a few settings that the techie gives you, and then you forget about it. PGP Sync takes care of everything else.

It works like this:

* The techie generates an "authority key". Then they create a list of PGP fingerprints that all members of your organization should keep updated, digitally sign this list with the authority key, and upload it to a website so that it's accessible from a public URL.
* All members of the organization install PGP Sync on their computers and configure it with the authority key's fingerprint and the URL of your signed fingerprint list. (Now, all of your members will automatically and regularly fetch this URL and then refresh all of the non-revoked keys on the list from a key server.)
* When new keys in your organization are added, the techie adds them to the fingerprint list, re-signs it with the authority key, and upload it to the same URL. If users migrate to new keys, the techie leaves their old fingerprints on the list so that all other members can tell that their old keys were revoked.

Now each member of your organization will have up-to-date public keys for each other member, and key changes will be transitioned smoothly without any further work or interaction.

Here are some features:

* Works in Mac OS X and Linux
* Creates system tray applet that launches automatically on boot
* Downloads from HKPS key server by default, but customizable
* Supports fetching fingerprints URL over Tor or other SOCKS5 proxies
* Makes sure non-revoked public keys are refreshed once a day
* Works seamlessly with the web of trust

## How is PGP Sync different than S/MIME, or running a Certificate Authority for PGP keys?

PGP Sync does one thing: Makes sure members of an organization always have up-to-date public keys from a centrally-managed list.

Unlike with S/MIME or CAs, users don't need to trust the central authority. At worst, a malicious authority could make you download fake public keys. If you manually verify fingerprints and sign keys, your OpenPGP software should pick the correct key to encrypt to each time. If you don't manually verify fingerprints and sign keys, then at least you won't be automatically encrypting to people's old revoked keys, and you'll get the latest keys for new members of your organization without having to manually find them and import them.

If you trust the person who manages the authority key, you could even sign it and set an `ownertrust` to `Full`. If the authority key cross-signs the keys of everyone in your organization, you'll have an internal web of trust, and can have much stronger confidence in all of the keys, even without requiring everyone to sign everyone else's key (a decentralized process that requires exponentially more work with each person who joins the organization).

S/MIME might be a better option than OpenPGP for some organizations. But PGP has the advantage that it's more popular, it doesn't require trusting a central authority, and it's simpler to use when communicating securely with people across multiple organizations.

## Creating the fingerprints file

First you must generate an authority key. For higher security, I recommend that you store this key on an OpenPGP smart card such as a Yubikey. Here's an example authority key:

```sh
$ gpg2 --list-keys --fingerprint "PGP Sync Example Authority"
pub   rsa4096/980EA13A 2016-07-07 [SC] [expires: 2017-07-07]
      Key fingerprint = 2646 A274 C86C 618D 6DB9  23A1 F0B6 DC77 980E A13A
uid         [ultimate] PGP Sync Example Authority
sub   rsa4096/9484EB1D 2016-07-07 [E] [expires: 2017-07-07]
```

Now create a list of all of the fingerprints that your organization uses. I recommend that you manually compare each person's fingerprint before adding it to this list. And while this isn't required by PGP Sync, it's a good idea to sign each person's key with your authority key, and have them sign the authority key back, so you can build an internal web of trust.

Each fingerprint should have its own line. Spaces within fingerprints are optional. Comments (which start with `#` characters) and whitespace is ignored, so feel free to mark up your fingerprints file with notes. Here's my example `fingerprints.txt`.

```
# Micah Lee
927F 419D 7EC8 2C2F 149C  1BD1 403C 2657 CD99 4F73 # current
0B14 9192 9806 5962 5470  0155 FD72 0AD9 EBA3 4B1C # old, revoked

# TODO: add other keys

# First Look warrant canary key
91C0 C982 A41F 8D39 3953  1A71 FAB7 37F9 C5C1 CA80
```

Next, clearsign your list of fingerprints using your authority key. Here's how I'm doing it in my example:

```sh
$ gpg2 -u 980EA13A --clearsign fingerprints.txt
```

And I end up with a signed version of `fingerprint.txt` called `fingerprints.txt.asc`:

```
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA256

# Micah Lee
927F 419D 7EC8 2C2F 149C  1BD1 403C 2657 CD99 4F73 # current
0B14 9192 9806 5962 5470  0155 FD72 0AD9 EBA3 4B1C # old, revoked

# TODO: add other keys

# First Look warrant canary key
91C0 C982 A41F 8D39 3953  1A71 FAB7 37F9 C5C1 CA80
-----BEGIN PGP SIGNATURE-----
Version: GnuPG v2

iQIcBAEBCAAGBQJXfraEAAoJEPC23HeYDqE6E8AP/AkheYSq6etx1fsdBdbDQHrR
2DDDeXbjPwGxy9BAHynVKqxqxUyouTmHi2V5yKQUQ7IX7RMmXONINQOaZlmSnpF+
Tc7VgjD6dJpz67fSnUtx6YeivMtO8a5VEMvr2fg2E/a1+gYEdL7biF17eQdp1Htg
N4XozwpE1DrI0sll8VwSiCbloOmpFofQpVYZCVEg28gq8yGB5Wz0y/f45gCLHoAd
jR5VpTsdBSZDA/Ty63ciaZn2QPdu0XCsB1CVrnmN3LgU2uGIjbNAOoHWLNQ2kexm
n8aeKaARH431cVK/76ouNYS4LDPnKYWm9MpCwT2gmulCuaPBtAT3FXxi8r+2Rmok
Z1JoxRYvmibsVT8tAF3fWctkI1trNZKtwygPHnJNKhXenwpoCfovWiap3rc8VFa1
2YScsoN83JKESjD9MoGC0rfQK8bJM+zI+0AveC7D+7jryQGBSf2wtKdH5iLkBKCn
g39sN3nSwNCN2VOakxI98ORq5gauByt1d8Cd584gnjMEydwqi58u6e1ngHerwxYk
aFuNY8Ozoe1IwAn+zYzcgTfce4y6808kA4xWQwxoi4QpNFM6gM9MWQ7j809/aprv
kqtxNFU8eXiOda5IBSIB0cOoZMo5hqmTZn+rAtHZ3KPkN5V8ZbvI3vJKl7CxJXLt
Mw4F3dk/+Xs9XnEh3R2q
=wdmj
-----END PGP SIGNATURE-----
```

Finally, upload `fingerprints.txt.asc` to a website (if you'd like, you could maintain this file in a public git repository) and make a note of the URL, as well as the authority key fingerprint. You'll need to give these two pieces of information to each member of your organization in order to configure PGP Sync on their computers.

Each time there is a key change in your organization, you need to add the new fingerprints to `fingerprints.txt`, re-sign it with your authority key, and re-upload it to the same URL.

## Configuring PGP Sync on everyone's computers

![Screenshot](/logo/screenshot.png)

Each list of fingerprints that you'd like PGP Sync to keep refreshed is called an endpoint, and you can have as many as you'd like (for example, if you belong to multiple organizations). To get started, all you need to do is add an endpoint and specify the `Signing key fingerprint` and the `Signed fingerprints URL`, and click the save button. PGP Sync will verify that the fingerprints file has been set up correctly, and if so, immediately sync the endpoint.

That's it. Just leave PGP Sync open in the background, and it will make sure all of your PGP keys get synced at least once a day.

### Using PGP Sync with Tor

It's simple to configure PGP Sync to download the fingerprints URL and refresh public keys from key servers using the Tor network. First, you need to install a system Tor on your computer.

* **Mac OS X:** The easiest way to install Tor and have it always run in the background in OS X is by using [Homebrew](http://brew.sh/). Install it if you don't already have it. Then install Tor and configure it to run in the background by typing this into your terminal:

  ```sh
  $ brew install tor
  $ brew services start tor
  ```

* **Linux:** Make sure you have a system Tor installed in the background. In Debian or Ubuntu, you can run `sudo apt install tor` to install it.

Now edit your PGP Sync endpoint and check the box next to `Load URL through SOCKS5 proxy (e.g. Tor)`. Leave the host as `127.0.0.1` and the port as `9050`, and save.
