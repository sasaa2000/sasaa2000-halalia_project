"""
HALALIA Runtime Contract

This document defines the official execution flow
inside the HALALIA Framework.

Every Provider must follow this contract.
Every Parser must follow this contract.
Every Pipeline must follow this contract.

Version:
    Runtime v1.0
"""


class RuntimeContract:
    """
    Official Runtime Flow

    Keyword
        ↓

    Provider
        ↓

    HTML
        ↓

    Parser
        ↓

    List[Product]
        ↓

    Pipeline
        ↓

    List[Product]
        ↓

    Storage / Telegram / API
    """

    VERSION = "1.0"