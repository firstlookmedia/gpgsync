# -*- coding: utf-8 -*-

def test_valid_fp(common):
    assert common.valid_fp(b'734F 6E70 7434 ECA6 C007  E1AE 82BD 6C96 16DA BB79')
    assert common.valid_fp(b'734F 6E70 7434 ECA6 C007  e1ae 82bd 6c96 16da bb79')
    assert common.valid_fp(b'734F6E707434ECA6C007E1AE82BD6C9616DABB79')
    assert common.valid_fp(b'734 f6e70  7434eca6c007e 1ae82bd6 c9616dab b79')
    assert common.valid_fp(b'A'*40)

    assert not common.valid_fp(b'A'*41)
    assert not common.valid_fp(b'A'*10)
    assert not common.valid_fp(b'A'*39+b'G')


def test_clean_fp(common):
    assert common.clean_fp(b'734F 6E70 7434 ECA6 C007  E1AE 82BD 6C96 16DA BB79') == b'734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp(b'734F 6E70 7434 ECA6 C007  e1ae 82bd 6c96 16da bb79') == b'734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp(b'734F6E707434ECA6C007E1AE82BD6C9616DABB79') == b'734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp(b'734 f6e70  7434eca6c007e 1ae82bd6 c9616dab b79') == b'734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp(b' ab '*20) == b'AB'*20


def test_fp_to_keyid(common):
    assert common.fp_to_keyid(b'734F6E707434ECA6C007E1AE82BD6C9616DABB79') == b'0x82BD6C9616DABB79'
    assert common.fp_to_keyid(b'0'*24+b'1'*16) == b'0x'+b'1'*16


def test_clean_keyserver(common):
    assert common.clean_keyserver(b'pgp.mit.edu') == b'hkp://pgp.mit.edu:80'
    assert common.clean_keyserver(b'hkp://pgp.mit.edu') == b'hkp://pgp.mit.edu:80'
    assert common.clean_keyserver(b'hkps://hkps.pool.sks-keyservers.net/') == b'hkps://hkps.pool.sks-keyservers.net:443'
    assert common.clean_keyserver(b'hkps://hkps.pool.sks-keyservers.net:4444') == b'hkps://hkps.pool.sks-keyservers.net:4444'
    assert common.clean_keyserver(b'ldap://somekeyserver') == b'hkp://somekeyserver:80'
