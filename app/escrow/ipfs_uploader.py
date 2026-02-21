from __future__ import annotations

# IPFS upload is a network-dependent operation.
# In the MVP this module returns a deterministic stub CID so the rest of the
# escrow pipeline can be exercised offline.  Replace the body of
# `upload_to_ipfs` with a real IPFS client call (e.g. ipfshttpclient or
# web3.storage) when network access is available.

_STUB_PREFIX = "bafybeistub"


def upload_to_ipfs(content_hash: str) -> str:
    """Upload an audit artifact to IPFS and return its CID.

    Parameters
    ----------
    content_hash:
        The SHA-256 hex digest of the artifact to be pinned.

    Returns
    -------
    str
        The IPFS Content Identifier (CID) for the pinned artifact.
        In the offline stub, returns a reproducible placeholder CID.
    """
    # Stub: derive a placeholder CID from the first 32 chars of the hash.
    return f"{_STUB_PREFIX}{content_hash[:32]}"
