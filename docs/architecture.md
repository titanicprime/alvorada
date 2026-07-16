
# Architecture

Machine-readable artifacts in `schema/`, `dictionary/`, `profiles/`, `codebooks/`, and `examples/` are authoritative. Python code in `src/alvorada/` validates, canonicalizes, hashes, compresses, and replays those artifacts deterministically.
