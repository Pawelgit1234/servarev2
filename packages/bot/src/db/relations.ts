import { relations } from "drizzle-orm/relations";
import { players, playerSnapshots, servers, serverBotSnapshots, serverDynamicSnapshots, serverSessions, serverSnapshots, softwares, playerSessions, ips, ipPorts, subchunks, serverBotSnapshotResourcePackAssociations, resourcePacks, mods, serverSnapshotModAssociations, plugins, serverSnapshotPluginAssociations, serverBotSnapshotModAssociations } from "./schema";

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

export const serverBotSnapshotsRelations = relations(serverBotSnapshots, ({one, many}) => ({
	server: one(servers, {
		fields: [serverBotSnapshots.serverId],
		references: [servers.id]
	}),
	subchunks: many(subchunks),
	serverBotSnapshotResourcePackAssociations: many(serverBotSnapshotResourcePackAssociations),
	serverBotSnapshotModAssociations: many(serverBotSnapshotModAssociations),
}));

export const serversRelations = relations(servers, ({one, many}) => ({
	serverBotSnapshots: many(serverBotSnapshots),
	serverDynamicSnapshots: many(serverDynamicSnapshots),
	serverSessions: many(serverSessions),
	serverSnapshots: many(serverSnapshots),
	playerSessions: many(playerSessions),
	ip: one(ips, {
		fields: [servers.ipId],
		references: [ips.id]
	}),
}));

export const serverDynamicSnapshotsRelations = relations(serverDynamicSnapshots, ({one}) => ({
	server: one(servers, {
		fields: [serverDynamicSnapshots.serverId],
		references: [servers.id]
	}),
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

export const subchunksRelations = relations(subchunks, ({one}) => ({
	serverBotSnapshot: one(serverBotSnapshots, {
		fields: [subchunks.botSnapshotId],
		references: [serverBotSnapshots.id]
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
	serverBotSnapshotModAssociations: many(serverBotSnapshotModAssociations),
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

export const serverBotSnapshotModAssociationsRelations = relations(serverBotSnapshotModAssociations, ({one}) => ({
	serverBotSnapshot: one(serverBotSnapshots, {
		fields: [serverBotSnapshotModAssociations.botSnapshotId],
		references: [serverBotSnapshots.id]
	}),
	mod: one(mods, {
		fields: [serverBotSnapshotModAssociations.modId],
		references: [mods.id]
	}),
}));