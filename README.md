# PGP Sync

PGP Sync is designed to let users always have up-to-date PGP public keys for other members of their organization.

If you're part of an organization that uses PGP internally you might notice that it doesn't scale well. New people join and create new keys and existing people revoke their old keys and transition to new ones. It quickly becomes unwieldy to ensure that everyone has a copy of everyone else's current key, and that old revoked keys get refreshed to prevent users from accidentally using them.

PGP Sync solves this problem. It works like this:

* You generate an "authority key" for your organization. Then create a list of PGP fingerprints that you want all members of your organization to keep updated, sign it with the authority key, and upload it to a website so that it's accessible from a public URL.
* Install PGP Sync on all of your organization member computers and configure it with the authority key's fingerprint and the URL of your signed fingerprint list. Now, all of your members will automatically fetch this URL and refresh all non-revoked keys on the list from a key server.
* When new keys in your organization are added, add them to the end of the fingerprint list, re-sign it with the authority key, and upload it to the same URL. If users migrate to new keys, make sure their old fingerprints remain on the list so that all other members can tell that their old keys were revoked.

Now each member of your organization will have up-to-date public keys for each other member, and key changes will be transitioned smoothly without any further work or interaction.

Here are some features:

* Works in Mac OS X and Linux
* Creates system tray applet that launches automatically on boot
* Downloads from HKPS keyserver by default, but customizable
* Supports fetching fingerprints URL over Tor or other SOCKS5 proxies
* Makes sure non-revoked public keys are refreshed once a day
* Works seamlessly with the web of trust

## How is PGP Sync different than S/MIME, or running a Certificate Authority for PGP keys?

PGP Sync does one thing: Makes sure members of an organization always have up-to-date public keys from a centrally-managed list.

Unlike with S/MIME and or CAs, users don't need to trust the central authority. At worst, a malicious authority would make you download fake public keys. If you manually verify fingerprints and sign keys, your OpenPGP software should pick the correct key to encrypt to each time. If you don't manually verify fingerprints and sign keys, then at least you won't be automatically encrypting to people's old revoked keys, and you'll get the latest keys for new members of your org without having to manually find them and import them.

If you trust the person who manages the authority key, you could even sign it and set an ownertrust to Full. As long as the authority key signs the keys of everyone in your org, you'll have an internal web of trust, and can have much stronger confidence in all of the keys, even without requiring everyone to sign everyone else's key (a decentralized process that requires exponentially more work with each person who joins the org).

S/MIME might be a better option than OpenPGP for some organizations. But PGP has the advantage that it's more popular, it doesn't require any trusting a central authority, and it's simpler to use when communicating securely with people from different organizations.

## Creating the fingerprints file

First you must generate an authority key. For higher security, I recommend that you store this key on an OpenPGP smart card. Here's the example authority key that I made:

```sh
$ gpg --fingerprint 39094117
pub   4096R/39094117 2015-09-03 [expires: 2016-09-02]
      Key fingerprint = AC9C 2809 8518 0E65 A277  4EA1 53FE 8D49 3909 4117
uid       [ultimate] GPG Authority
```

Now create a list of all of the fingerprints that your organization uses. I recommend that you manually compare each person's fingerprint before adding it to this list. And while this isn't required by PGP Sync, it's a good idea to sign each person's key with your authority key, so you can build an internal web of trust.

Spaces are optional, and separate each fingerprint with newlines. Comments (which start with "#" signs) and whitespace is all ignored, so feel free to mark up your fingerprints file with notes. Here's my example `fingerprints.txt`.

```
927F 419D 7EC8 2C2F 149C  1BD1 403C 2657 CD99 4F73
0B14 9192 9806 5962 5470  0155 FD72 0AD9 EBA3 4B1C
5F92 3DAC 0B16 B1F9 7CB3  C487 DD78 39DA D4D0 03DA
```

Next, clearsign your list of fingerprints using your authority key. Here's how I'm doing it in my example:

```sh
gpg -u 39094117 --clearsign fingerprints.txt
```

And I end up with a signed version of `fingerprint.txt` called `fingerprints.txt.asc`:

```
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

927F 419D 7EC8 2C2F 149C  1BD1 403C 2657 CD99 4F73
0B14 9192 9806 5962 5470  0155 FD72 0AD9 EBA3 4B1C
5F92 3DAC 0B16 B1F9 7CB3  C487 DD78 39DA D4D0 03DA
-----BEGIN PGP SIGNATURE-----

iQIcBAEBCgAGBQJV58juAAoJEFP+jUk5CUEX4UsP/28nxx87mXGIXs2ZkLWsqLIG
3hslxMIM/y30LQXDKMPjthgWvddU7p/E7vGIRSWi/r0pf+uIowNCd0mZviWa/dCq
bTbXfiyO0mnajOvJYdTFEAQpYk4aF9++KbmO2jl9pt/j99//f8dcqa5R976oqhao
4Cf+mkOdV2znVGvFgpnCyw2bceT6bnj/RHJ3uHSP6Jzo0jievzgg+FVjnUveyvLh
Bq+52m/XEZat+Nxs3CEC9lylTeWfdNzDZy6wuETjI6Evyx3jUWdkNEbW1mDDcG13
vuWKF/F5kaRM7DxI2wM67+dYD26C4JRW0bJwpr02zNlMhu98T5LZBlGP5ajHRvS9
iNw/pMOGjrSORBNL3ETaKt8Xc/16qUn6SSINqeqwAZuT1ZrwJASA+6CK9fD+YMDf
/uFdPl7Lc1Yx+/i61XexieqMJ13Dj1BfPYcKJe49kQNkwGGWPvHJli6/l6+oQ8ii
0CkcXAV+EiWyaVY8SaL5HrpX/HfBOdZDDFbwBNUjdrnifl2tc66X81jJk9RDKrbt
mgCJ/gpzCSvI8PNUOSFVs7XHMBF248b9b+JKhBsFVcTof8u3VMcf1hzug2UUOU9r
ehRcaAI3djC5+TGFq9Jtlt5ZWNzsxJx8Z0XdbmwX2pz3Nvvm+C3JPHQCl+oZ7jvU
MoRT/WQGfmuCXAZFgyAT
=7ta4
-----END PGP SIGNATURE-----
```

Finally, upload `fingerprints.txt.asc` to a website and make a note of the URL, as well as the authority key fingerprint. You'll need to give these two pieces of information to each member of your organization in order to configure PGP Sync on their computers.

Each time there is a key change in your organization, you need to add the new fingerprints to `fingerprints.txt`, re-sign it with your authority key, and re-upload it to the same URL.

## Configuring PGP Sync on everyone's computers

TODO: Add screenshot and instructions.
