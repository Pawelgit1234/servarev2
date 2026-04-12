from enum import Enum


class ServerType(Enum):
    LEGACY = "legacy"  # beta 1.8 - 1.6
    JAVA = "java"  # 1.7+
    BEDROCK = "bedrock"
