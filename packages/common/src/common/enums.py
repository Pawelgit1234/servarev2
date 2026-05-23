from enum import Enum


class PlayerType(Enum):
    PREMIUM = "premium"
    OFFLINE = "offline"  # = cracked
    BEDROCK = "bedrock"


class ServerType(Enum):
    LEGACY = "legacy"  # beta 1.8 - 1.6
    JAVA = "java"  # 1.7+
    BEDROCK = "bedrock"


class AssetField(Enum):
    ICON = "icon"
    SKIN = "skin"
    CAPE = "cape"


class ProtocolType(Enum):
    TCP = "tcp"
    UDP = "udp"


class DetectedServiceType(Enum):
    # Maps
    BLUEMAP = "bluemap"
    DYNMAP = "dynmap"
    PL3XMAP = "pl3xmap"
    SQUAREMAP = "squaremap"

    # Panels
    AMP = "amp"
    PTERODACTYL = "pterodactyl"
    PELICAN = "pelican"
    MULTICRAFT = "multicraft"
    CRAFTY = "crafty"

    # Other
    GENERIC_HTTP = "generic_http"
    UNKNOWN = "unknown"


class ServerSoftwareType(Enum):
    VANILLA = "vanilla"

    FORGE = "forge"
    FABRIC = "fabric"
    QUILT = "quilt"
    NEOFORGE = "neoforge"

    PAPER = "paper"
    PURPUR = "purpur"
    PUFFERFISH = "pufferfish"
    TUINITY = "tuinity"
    AIRPLANE = "airplane"
    SPIGOT = "spigot"
    CRAFTBUKKIT = "craftbukkit"
    BUKKIT = "bukkit"

    VELOCITY = "velocity"
    WATERFALL = "waterfall"
    BUNGEE = "bungee"

    SPONGE = "sponge"
    SPONGEFORGE = "spongeforge"
    SPONGEVANILLA = "spongevanilla"

    ARCLIGHT = "arclight"
    MOHIST = "mohist"
    MAGMA = "magma"
    CATSERVER = "catserver"
