import json
import struct
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from apps.media.offline.tasks import MAGIC

# reuse helpers from above: _unpack functions
_unpack_u32 = lambda b: struct.unpack(">I", b)[0]
_unpack_u16 = lambda b: struct.unpack(">H", b)[0]
_unpack_u64 = lambda b: struct.unpack(">Q", b)[0]


def _derive_keys_from_dek(dek: bytes, info: bytes = b"podcast-offline-package", length: int = 64):
    hkdf = HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=info)
    okm = hkdf.derive(dek)
    enc_key = okm[:32]
    mac_key = okm[32:64]
    return enc_key, mac_key


def stream_decrypt_package(fileobj, plaintext_dek: bytes, out_writer):
    """
    fileobj: a file-like object opened in 'rb' at position 0 (the package)
    plaintext_dek: bytes (the DEK obtained by KMS.Decrypt) - MUST be protected
    out_writer: file-like object opened 'wb' or a callback that accepts bytes to write decrypted payload
    """
    # read magic
    magic = fileobj.read(8)
    if magic != MAGIC:
        raise RuntimeError("Invalid package magic")

    # manifest len + manifest
    mlen_bytes = fileobj.read(4)
    mlen = _unpack_u32(mlen_bytes)
    manifest_json = fileobj.read(mlen)
    manifest = json.loads(manifest_json.decode("utf-8"))

    # read iv_prefix
    iv_prefix = fileobj.read(8)

    enc_key, mac_key = _derive_keys_from_dek(plaintext_dek)

    # iterate chunks
    while True:
        idx_bytes = fileobj.read(8)
        if not idx_bytes:
            break  # EOF
        chunk_index = _unpack_u64(idx_bytes)
        iv_len = _unpack_u16(fileobj.read(2))
        iv = fileobj.read(iv_len)
        ct_len = _unpack_u32(fileobj.read(4))
        ct = fileobj.read(ct_len)
        tag_len = _unpack_u16(fileobj.read(2))
        tag = fileobj.read(tag_len)

        # verify HMAC
        h = hmac.HMAC(mac_key, hashes.SHA256())
        h.update(chunk_index.to_bytes(8, "big"))
        h.update(iv)
        h.update(ct)
        try:
            h.verify(tag)
        except Exception as exc:
            raise RuntimeError("HMAC verification failed") from exc

        # decrypt AES-CTR
        cipher = Cipher(algorithms.AES(enc_key), modes.CTR(iv))
        decryptor = cipher.decryptor()
        pt = decryptor.update(ct) + decryptor.finalize()

        # write plaintext chunk to out_writer
        out_writer.write(pt)

    # done
    return manifest
