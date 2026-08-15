import { pgTable, unique, serial, varchar, timestamp, index, foreignKey, integer, doublePrecision, boolean, primaryKey, pgEnum } from "drizzle-orm/pg-core"
import { sql } from "drizzle-orm"

export const detectedservicetype = pgEnum("detectedservicetype", ['BLUEMAP', 'DYNMAP', 'PL3XMAP', 'SQUAREMAP', 'AMP', 'PTERODACTYL', 'PELICAN', 'MULTICRAFT', 'CRAFTY', 'GENERIC_HTTP', 'UNKNOWN'])
export const playertype = pgEnum("playertype", ['PREMIUM', 'OFFLINE', 'BEDROCK'])
export const protocoltype = pgEnum("protocoltype", ['TCP', 'UDP'])
export const serversoftwaretype = pgEnum("serversoftwaretype", ['VANILLA', 'FORGE', 'FABRIC', 'QUILT', 'NEOFORGE', 'PAPER', 'PURPUR', 'PUFFERFISH', 'TUINITY', 'AIRPLANE', 'SPIGOT', 'CRAFTBUKKIT', 'BUKKIT', 'VELOCITY', 'WATERFALL', 'BUNGEE', 'SPONGE', 'SPONGEFORGE', 'SPONGEVANILLA', 'ARCLIGHT', 'MOHIST', 'MAGMA', 'CATSERVER'])
export const servertype = pgEnum("servertype", ['LEGACY', 'JAVA', 'BEDROCK'])


export const resourcePacks = pgTable("resource_packs", {
	id: serial().primaryKey().notNull(),
	url: varchar({ length: 512 }).notNull(),
	hash: varchar({ length: 64 }).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	unique("resource_packs_url_key").on(table.url),
]);

export const plugins = pgTable("plugins", {
	id: serial().primaryKey().notNull(),
	name: varchar({ length: 128 }).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_plugins_name").using("btree", table.name.asc().nullsLast().op("text_ops")),
	unique("plugins_name_key").on(table.name),
]);

export const alembicVersion = pgTable("alembic_version", {
	versionNum: varchar("version_num", { length: 32 }).primaryKey().notNull(),
});

export const players = pgTable("players", {
	id: serial().primaryKey().notNull(),
	playerType: playertype("player_type").notNull(),
	uuid: varchar().notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	lastSeenAt: timestamp("last_seen_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_players_created_at").using("btree", table.createdAt.asc().nullsLast().op("timestamptz_ops")),
	index("ix_players_player_type").using("btree", table.playerType.asc().nullsLast().op("enum_ops")),
]);

export const playerSnapshots = pgTable("player_snapshots", {
	id: serial().primaryKey().notNull(),
	playerId: integer("player_id").notNull(),
	name: varchar({ length: 16 }).notNull(),
	skin: varchar({ length: 32 }),
	cape: varchar({ length: 32 }),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_player_snapshots_name").using("btree", table.name.asc().nullsLast().op("text_ops")),
	index("ix_player_snapshots_player_id").using("btree", table.playerId.asc().nullsLast().op("int4_ops")),
	index("ix_player_snapshots_player_id_created_at").using("btree", table.playerId.asc().nullsLast().op("int4_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	foreignKey({
			columns: [table.playerId],
			foreignColumns: [players.id],
			name: "player_snapshots_player_id_fkey"
		}).onDelete("cascade"),
]);

export const serverBotSnapshots = pgTable("server_bot_snapshots", {
	id: serial().primaryKey().notNull(),
	serverId: integer("server_id").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_server_bot_snapshots_server_id").using("btree", table.serverId.asc().nullsLast().op("int4_ops")),
	index("ix_server_bot_snapshots_server_id_created_at").using("btree", table.serverId.asc().nullsLast().op("int4_ops"), table.createdAt.desc().nullsFirst().op("int4_ops")),
	foreignKey({
			columns: [table.serverId],
			foreignColumns: [servers.id],
			name: "server_bot_snapshots_server_id_fkey"
		}).onDelete("cascade"),
]);

export const serverDynamicSnapshots = pgTable("server_dynamic_snapshots", {
	id: serial().primaryKey().notNull(),
	serverId: integer("server_id").notNull(),
	playersOnline: integer("players_online").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_server_dynamic_snapshots_players_online").using("btree", table.playersOnline.asc().nullsLast().op("int4_ops")),
	index("ix_server_dynamic_snapshots_server_id").using("btree", table.serverId.asc().nullsLast().op("int4_ops")),
	index("ix_server_dynamic_snapshots_server_id_created_at").using("btree", table.serverId.asc().nullsLast().op("int4_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	foreignKey({
			columns: [table.serverId],
			foreignColumns: [servers.id],
			name: "server_dynamic_snapshots_server_id_fkey"
		}).onDelete("cascade"),
]);

export const serverSessions = pgTable("server_sessions", {
	id: serial().primaryKey().notNull(),
	serverId: integer("server_id").notNull(),
	from: timestamp("from_", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	to: timestamp({ withTimezone: true, mode: 'string' }),
}, (table) => [
	index("ix_server_sessions_server_id").using("btree", table.serverId.asc().nullsLast().op("int4_ops")),
	index("ix_server_sessions_server_id_from_desc").using("btree", table.serverId.asc().nullsLast().op("int4_ops"), table.from.desc().nullsFirst().op("int4_ops")),
	foreignKey({
			columns: [table.serverId],
			foreignColumns: [servers.id],
			name: "server_sessions_server_id_fkey"
		}).onDelete("cascade"),
]);

export const mods = pgTable("mods", {
	id: serial().primaryKey().notNull(),
	name: varchar({ length: 128 }).notNull(),
	version: varchar({ length: 32 }).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_mods_name").using("btree", table.name.asc().nullsLast().op("text_ops")),
	index("ix_mods_name_version").using("btree", table.name.asc().nullsLast().op("text_ops"), table.version.asc().nullsLast().op("text_ops")),
]);

export const serverSnapshots = pgTable("server_snapshots", {
	id: serial().primaryKey().notNull(),
	serverId: integer("server_id").notNull(),
	version: varchar({ length: 32 }).notNull(),
	playersMax: integer("players_max").notNull(),
	motd: varchar({ length: 512 }).notNull(),
	latency: doublePrecision().notNull(),
	protocol: integer(),
	enforcesSecureChat: boolean(),
	fmlNetworkVersion: integer("fml_network_version"),
	modsTruncated: boolean("mods_truncated"),
	mapName: varchar("map_name", { length: 64 }),
	gamemode: varchar({ length: 32 }),
	softwareId: integer("software_id"),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	icon: varchar({ length: 32 }),
}, (table) => [
	index("ix_server_snapshots_icon").using("btree", table.icon.asc().nullsLast().op("text_ops")),
	index("ix_server_snapshots_players_max").using("btree", table.playersMax.asc().nullsLast().op("int4_ops")),
	index("ix_server_snapshots_server_id").using("btree", table.serverId.asc().nullsLast().op("int4_ops")),
	index("ix_server_snapshots_server_id_created_at").using("btree", table.serverId.asc().nullsLast().op("timestamptz_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	index("ix_server_snapshots_software_id").using("btree", table.softwareId.asc().nullsLast().op("int4_ops")),
	index("ix_server_snapshots_version").using("btree", table.version.asc().nullsLast().op("text_ops")),
	foreignKey({
			columns: [table.serverId],
			foreignColumns: [servers.id],
			name: "server_snapshots_server_id_fkey"
		}).onDelete("cascade"),
	foreignKey({
			columns: [table.softwareId],
			foreignColumns: [softwares.id],
			name: "server_snapshots_software_id_fkey"
		}).onDelete("set null"),
]);

export const softwares = pgTable("softwares", {
	id: serial().primaryKey().notNull(),
	name: serversoftwaretype().notNull(),
	version: varchar({ length: 32 }).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_softwares_name").using("btree", table.name.asc().nullsLast().op("enum_ops")),
	index("ix_softwares_version").using("btree", table.version.asc().nullsLast().op("text_ops")),
]);

export const playerSessions = pgTable("player_sessions", {
	id: serial().primaryKey().notNull(),
	playerId: integer("player_id").notNull(),
	from: timestamp("from_", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	to: timestamp({ mode: 'string' }),
	serverId: integer("server_id").notNull(),
}, (table) => [
	index("ix_player_sessions_player_id").using("btree", table.playerId.asc().nullsLast().op("int4_ops")),
	index("ix_player_sessions_player_id_from_desc").using("btree", table.playerId.asc().nullsLast().op("int4_ops"), table.from.desc().nullsFirst().op("timestamptz_ops")),
	index("ix_player_sessions_server_id").using("btree", table.serverId.asc().nullsLast().op("int4_ops")),
	index("ix_player_sessions_server_id_from_desc").using("btree", table.serverId.asc().nullsLast().op("int4_ops"), table.from.desc().nullsFirst().op("timestamptz_ops")),
	foreignKey({
			columns: [table.playerId],
			foreignColumns: [players.id],
			name: "player_sessions_player_id_fkey"
		}).onDelete("cascade"),
	foreignKey({
			columns: [table.serverId],
			foreignColumns: [servers.id],
			name: "player_sessions_server_id_fkey"
		}).onDelete("cascade"),
]);

export const ipPorts = pgTable("ip_ports", {
	id: serial().primaryKey().notNull(),
	ipId: integer("ip_id").notNull(),
	port: integer().notNull(),
	protocolType: protocoltype("protocol_type").notNull(),
	detectedServiceType: detectedservicetype("detected_service_type").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_ip_ports_detected_service_type").using("btree", table.detectedServiceType.asc().nullsLast().op("enum_ops")),
	index("ix_ip_ports_ip_id").using("btree", table.ipId.asc().nullsLast().op("int4_ops")),
	index("ix_ip_ports_protocol_type_port").using("btree", table.protocolType.asc().nullsLast().op("int4_ops"), table.port.asc().nullsLast().op("int4_ops")),
	foreignKey({
			columns: [table.ipId],
			foreignColumns: [ips.id],
			name: "ip_ports_ip_id_fkey"
		}).onDelete("cascade"),
]);

export const subchunks = pgTable("subchunks", {
	id: serial().primaryKey().notNull(),
	botSnapshotId: integer("bot_snapshot_id").notNull(),
	hash: varchar({ length: 32 }).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_subchunks_bot_snapshot_id").using("btree", table.botSnapshotId.asc().nullsLast().op("int4_ops")),
	index("ix_subchunks_hash").using("btree", table.hash.asc().nullsLast().op("text_ops")),
	foreignKey({
			columns: [table.botSnapshotId],
			foreignColumns: [serverBotSnapshots.id],
			name: "subchunks_bot_snapshot_id_fkey"
		}).onDelete("cascade"),
]);

export const ips = pgTable("ips", {
	id: serial().primaryKey().notNull(),
	ip: varchar().notNull(),
	lastIpCheckAt: timestamp("last_ip_check_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	lastPorterCheckAt: timestamp("last_porter_check_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	country: varchar({ length: 2 }),
	region: varchar({ length: 100 }),
	city: varchar({ length: 100 }),
	latitude: doublePrecision(),
	longitude: doublePrecision(),
	hostname: varchar({ length: 255 }),
	asn: varchar({ length: 150 }),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	lastSeenAt: timestamp("last_seen_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	isMultiport: boolean("is_multiport").notNull(),
}, (table) => [
	unique("ips_ip_key").on(table.ip),
]);

export const servers = pgTable("servers", {
	id: serial().primaryKey().notNull(),
	port: integer().notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	isLan: boolean("is_lan").notNull(),
	serverType: servertype("server_type").notNull(),
	ipId: integer("ip_id").notNull(),
	lastBotCheckAt: timestamp("last_bot_check_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_servers_created_at").using("btree", table.createdAt.asc().nullsLast().op("timestamptz_ops")),
	index("ix_servers_ip_id").using("btree", table.ipId.asc().nullsLast().op("int4_ops")),
	index("ix_servers_port").using("btree", table.port.asc().nullsLast().op("int4_ops")),
	index("ix_servers_server_type").using("btree", table.serverType.asc().nullsLast().op("enum_ops")),
	foreignKey({
			columns: [table.ipId],
			foreignColumns: [ips.id],
			name: "servers_ip_id_fkey"
		}).onDelete("cascade"),
]);

export const serverBotSnapshotResourcePackAssociations = pgTable("server_bot_snapshot_resource_pack_associations", {
	botSnapshotId: integer("bot_snapshot_id").notNull(),
	resourcePackId: integer("resource_pack_id").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_bot_rp_pack_id").using("btree", table.resourcePackId.asc().nullsLast().op("int4_ops")),
	index("ix_bot_rp_snapshot_id").using("btree", table.botSnapshotId.asc().nullsLast().op("int4_ops")),
	foreignKey({
			columns: [table.botSnapshotId],
			foreignColumns: [serverBotSnapshots.id],
			name: "server_bot_snapshot_resource_pack_associat_bot_snapshot_id_fkey"
		}).onDelete("cascade"),
	foreignKey({
			columns: [table.resourcePackId],
			foreignColumns: [resourcePacks.id],
			name: "server_bot_snapshot_resource_pack_associa_resource_pack_id_fkey"
		}).onDelete("cascade"),
	primaryKey({ columns: [table.resourcePackId, table.botSnapshotId], name: "server_bot_snapshot_resource_pack_associations_pkey"}),
]);

export const serverSnapshotModAssociations = pgTable("server_snapshot_mod_associations", {
	snapshotId: integer("snapshot_id").notNull(),
	modId: integer("mod_id").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_ss_mod_mod_id").using("btree", table.modId.asc().nullsLast().op("int4_ops")),
	index("ix_ss_mod_snapshot_id").using("btree", table.snapshotId.asc().nullsLast().op("int4_ops")),
	foreignKey({
			columns: [table.modId],
			foreignColumns: [mods.id],
			name: "server_snapshot_mod_associations_mod_id_fkey"
		}).onDelete("cascade"),
	foreignKey({
			columns: [table.snapshotId],
			foreignColumns: [serverSnapshots.id],
			name: "server_snapshot_mod_associations_server_snapshot_id_fkey"
		}).onDelete("cascade"),
	primaryKey({ columns: [table.snapshotId, table.modId], name: "server_snapshot_mod_associations_pkey"}),
]);

export const serverSnapshotPluginAssociations = pgTable("server_snapshot_plugin_associations", {
	snapshotId: integer("snapshot_id").notNull(),
	pluginId: integer("plugin_id").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_ss_plugin_plugin_id").using("btree", table.pluginId.asc().nullsLast().op("int4_ops")),
	index("ix_ss_plugin_snapshot_id").using("btree", table.snapshotId.asc().nullsLast().op("int4_ops")),
	foreignKey({
			columns: [table.pluginId],
			foreignColumns: [plugins.id],
			name: "server_snapshot_plugin_associations_plugin_id_fkey"
		}).onDelete("cascade"),
	foreignKey({
			columns: [table.snapshotId],
			foreignColumns: [serverSnapshots.id],
			name: "server_snapshot_plugin_associations_server_snapshot_id_fkey"
		}).onDelete("cascade"),
	primaryKey({ columns: [table.snapshotId, table.pluginId], name: "server_snapshot_plugin_associations_pkey"}),
]);

export const serverBotSnapshotModAssociations = pgTable("server_bot_snapshot_mod_associations", {
	botSnapshotId: integer("bot_snapshot_id").notNull(),
	modId: integer("mod_id").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
}, (table) => [
	index("ix_bot_mod_mod_id").using("btree", table.modId.asc().nullsLast().op("int4_ops")),
	index("ix_bot_mod_snapshot_id").using("btree", table.botSnapshotId.asc().nullsLast().op("int4_ops")),
	foreignKey({
			columns: [table.botSnapshotId],
			foreignColumns: [serverBotSnapshots.id],
			name: "server_bot_snapshot_mod_associations_bot_snapshot_id_fkey"
		}).onDelete("cascade"),
	foreignKey({
			columns: [table.modId],
			foreignColumns: [mods.id],
			name: "server_bot_snapshot_mod_associations_mod_id_fkey"
		}).onDelete("cascade"),
	primaryKey({ columns: [table.modId, table.botSnapshotId], name: "server_bot_snapshot_mod_associations_pkey"}),
]);
