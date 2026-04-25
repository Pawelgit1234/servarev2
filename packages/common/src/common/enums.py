from enum import Enum


class PlayerType(Enum):
    PREMIUM = "premium"
    OFFLINE = "offline"  # = cracked
    BEDROCK = "bedrock"


class ServerType(Enum):
    LEGACY = "legacy"  # beta 1.8 - 1.6
    JAVA = "java"  # 1.7+
    BEDROCK = "bedrock"
