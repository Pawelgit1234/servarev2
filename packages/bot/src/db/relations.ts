import { relations } from "drizzle-orm/relations";
import { players, playerSnapshots, servers, serverDynamicSnapshots, serverSessions, serverSnapshots, softwares, playerSessions, ips, ipPorts, serverBotSnapshots, log4Shells, serverBotSnapshotResourcePackAssociations, resourcePacks, mods, serverSnapshotModAssociations, plugins, serverSnapshotPluginAssociations } from "./schema";

export const playerSnapshotsRelations = relations(playerSnapshots, ({one}) => ({
	player: one(players, {
		fields: [playerSnapshots.playerId],
		references: [players.id]
	}),
}));

export const playersRelations = relations(players, ({many}) => ({
	playerSnapshots: many(playerSnapshots),
	playerSessions: many(playerSessions),
}));

export const serverDynamicSnapshotsRelations = relations(serverDynamicSnapshots, ({one}) => ({
	server: one(servers, {
		fields: [serverDynamicSnapshots.serverId],
		references: [servers.id]
	}),
}));

export const serversRelations = relations(servers, ({one, many}) => ({
	serverDynamicSnapshots: many(serverDynamicSnapshots),
	serverSessions: many(serverSessions),
	serverSnapshots: many(serverSnapshots),
	playerSessions: many(playerSessions),
	ip: one(ips, {
		fields: [servers.ipId],
		references: [ips.id]
	}),
	serverBotSnapshots: many(serverBotSnapshots),
	log4Shells: many(log4Shells),
}));

export const serverSessionsRelations = relations(serverSessions, ({one}) => ({
	server: one(servers, {
		fields: [serverSessions.serverId],
		references: [servers.id]
	}),
}));

export const serverSnapshotsRelations = relations(serverSnapshots, ({one, many}) => ({
	server: one(servers, {
		fields: [serverSnapshots.serverId],
		references: [servers.id]
	}),
	software: one(softwares, {
		fields: [serverSnapshots.softwareId],
		references: [softwares.id]
	}),
	serverSnapshotModAssociations: many(serverSnapshotModAssociations),
	serverSnapshotPluginAssociations: many(serverSnapshotPluginAssociations),
}));

export const softwaresRelations = relations(softwares, ({many}) => ({
	serverSnapshots: many(serverSnapshots),
}));

export const playerSessionsRelations = relations(playerSessions, ({one}) => ({
	player: one(players, {
		fields: [playerSessions.playerId],
		references: [players.id]
	}),
	server: one(servers, {
		fields: [playerSessions.serverId],
		references: [servers.id]
	}),
}));

export const ipPortsRelations = relations(ipPorts, ({one}) => ({
	ip: one(ips, {
		fields: [ipPorts.ipId],
		references: [ips.id]
	}),
}));

export const ipsRelations = relations(ips, ({many}) => ({
	ipPorts: many(ipPorts),
	servers: many(servers),
}));

export const serverBotSnapshotsRelations = relations(serverBotSnapshots, ({one, many}) => ({
	server: one(servers, {
		fields: [serverBotSnapshots.serverId],
		references: [servers.id]
	}),
	serverBotSnapshotResourcePackAssociations: many(serverBotSnapshotResourcePackAssociations),
}));

export const log4ShellsRelations = relations(log4Shells, ({one}) => ({
	server: one(servers, {
		fields: [log4Shells.serverId],
		references: [servers.id]
	}),
}));

export const serverBotSnapshotResourcePackAssociationsRelations = relations(serverBotSnapshotResourcePackAssociations, ({one}) => ({
	serverBotSnapshot: one(serverBotSnapshots, {
		fields: [serverBotSnapshotResourcePackAssociations.botSnapshotId],
		references: [serverBotSnapshots.id]
	}),
	resourcePack: one(resourcePacks, {
		fields: [serverBotSnapshotResourcePackAssociations.resourcePackId],
		references: [resourcePacks.id]
	}),
}));

export const resourcePacksRelations = relations(resourcePacks, ({many}) => ({
	serverBotSnapshotResourcePackAssociations: many(serverBotSnapshotResourcePackAssociations),
}));

export const serverSnapshotModAssociationsRelations = relations(serverSnapshotModAssociations, ({one}) => ({
	mod: one(mods, {
		fields: [serverSnapshotModAssociations.modId],
		references: [mods.id]
	}),
	serverSnapshot: one(serverSnapshots, {
		fields: [serverSnapshotModAssociations.snapshotId],
		references: [serverSnapshots.id]
	}),
}));

export const modsRelations = relations(mods, ({many}) => ({
	serverSnapshotModAssociations: many(serverSnapshotModAssociations),
}));

export const serverSnapshotPluginAssociationsRelations = relations(serverSnapshotPluginAssociations, ({one}) => ({
	plugin: one(plugins, {
		fields: [serverSnapshotPluginAssociations.pluginId],
		references: [plugins.id]
	}),
	serverSnapshot: one(serverSnapshots, {
		fields: [serverSnapshotPluginAssociations.snapshotId],
		references: [serverSnapshots.id]
	}),
}));

export const pluginsRelations = relations(plugins, ({many}) => ({
	serverSnapshotPluginAssociations: many(serverSnapshotPluginAssociations),
}));