from nose import with_setup
from pgpsync import common

def test_valid_fp():
    assert common.valid_fp('734F 6E70 7434 ECA6 C007  E1AE 82BD 6C96 16DA BB79')
    assert common.valid_fp('734F 6E70 7434 ECA6 C007  e1ae 82bd 6c96 16da bb79')
    assert common.valid_fp('734F6E707434ECA6C007E1AE82BD6C9616DABB79')
    assert common.valid_fp('734 f6e70  7434eca6c007e 1ae82bd6 c9616dab b79')
    assert common.valid_fp('A'*40)

    assert not common.valid_fp('A'*41)
    assert not common.valid_fp('A'*10)
    assert not common.valid_fp('A'*39+'G')

def test_clean_fp():
    assert common.clean_fp('734F 6E70 7434 ECA6 C007  E1AE 82BD 6C96 16DA BB79') == '734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp('734F 6E70 7434 ECA6 C007  e1ae 82bd 6c96 16da bb79') == '734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp('734F6E707434ECA6C007E1AE82BD6C9616DABB79') == '734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp('734 f6e70  7434eca6c007e 1ae82bd6 c9616dab b79') == '734F6E707434ECA6C007E1AE82BD6C9616DABB79'
    assert common.clean_fp(' ab '*20) == 'AB'*20

def test_fp_to_keyid():
    assert common.fp_to_keyid('734F6E707434ECA6C007E1AE82BD6C9616DABB79') == '0x82BD6C9616DABB79'
    assert common.fp_to_keyid('0'*24+'1'*16) == '0x'+'1'*16

def test_clean_keyserver():
    assert common.clean_keyserver('pgp.mit.edu') == 'hkp://pgp.mit.edu'
    assert common.clean_keyserver('hkp://pgp.mit.edu') == 'hkp://pgp.mit.edu'
    assert common.clean_keyserver('ldap://somekeyserver') == 'ldap://somekeyserver'
