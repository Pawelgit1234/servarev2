-- Current sql file was generated after introspecting the database
-- If you want to run this migration please uncomment this code before executing migrations
/*
CREATE TYPE "public"."detectedservicetype" AS ENUM('BLUEMAP', 'DYNMAP', 'PL3XMAP', 'SQUAREMAP', 'AMP', 'PTERODACTYL', 'PELICAN', 'MULTICRAFT', 'CRAFTY', 'GENERIC_HTTP', 'UNKNOWN');--> statement-breakpoint
CREATE TYPE "public"."playertype" AS ENUM('PREMIUM', 'OFFLINE', 'BEDROCK');--> statement-breakpoint
CREATE TYPE "public"."protocoltype" AS ENUM('TCP', 'UDP');--> statement-breakpoint
CREATE TYPE "public"."serversoftwaretype" AS ENUM('VANILLA', 'FORGE', 'FABRIC', 'QUILT', 'NEOFORGE', 'PAPER', 'PURPUR', 'PUFFERFISH', 'TUINITY', 'AIRPLANE', 'SPIGOT', 'CRAFTBUKKIT', 'BUKKIT', 'VELOCITY', 'WATERFALL', 'BUNGEE', 'SPONGE', 'SPONGEFORGE', 'SPONGEVANILLA', 'ARCLIGHT', 'MOHIST', 'MAGMA', 'CATSERVER');--> statement-breakpoint
CREATE TYPE "public"."servertype" AS ENUM('LEGACY', 'JAVA', 'BEDROCK');--> statement-breakpoint
CREATE TABLE "resource_packs" (
	"id" serial PRIMARY KEY NOT NULL,
	"url" varchar(512) NOT NULL,
	"hash" varchar(64) NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "resource_packs_url_key" UNIQUE("url")
);
--> statement-breakpoint
CREATE TABLE "plugins" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" varchar(128) NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "plugins_name_key" UNIQUE("name")
);
--> statement-breakpoint
CREATE TABLE "alembic_version" (
	"version_num" varchar(32) PRIMARY KEY NOT NULL
);
--> statement-breakpoint
CREATE TABLE "players" (
	"id" serial PRIMARY KEY NOT NULL,
	"player_type" "playertype" NOT NULL,
	"uuid" varchar NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"last_seen_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "player_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"player_id" integer NOT NULL,
	"name" varchar(16) NOT NULL,
	"skin" varchar(32),
	"cape" varchar(32),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "server_bot_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"server_id" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "server_dynamic_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"server_id" integer NOT NULL,
	"players_online" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "server_sessions" (
	"id" serial PRIMARY KEY NOT NULL,
	"server_id" integer NOT NULL,
	"from_" timestamp with time zone DEFAULT now() NOT NULL,
	"to" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "mods" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" varchar(128) NOT NULL,
	"version" varchar(32) NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "server_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"server_id" integer NOT NULL,
	"version" varchar(32) NOT NULL,
	"players_max" integer NOT NULL,
	"motd" varchar(512) NOT NULL,
	"latency" double precision NOT NULL,
	"protocol" integer,
	"enforcesSecureChat" boolean,
	"fml_network_version" integer,
	"mods_truncated" boolean,
	"map_name" varchar(64),
	"gamemode" varchar(32),
	"software_id" integer,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"icon" varchar(32)
);
--> statement-breakpoint
CREATE TABLE "softwares" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" "serversoftwaretype" NOT NULL,
	"version" varchar(32) NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "player_sessions" (
	"id" serial PRIMARY KEY NOT NULL,
	"player_id" integer NOT NULL,
	"from_" timestamp with time zone DEFAULT now() NOT NULL,
	"to" timestamp,
	"server_id" integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ip_ports" (
	"id" serial PRIMARY KEY NOT NULL,
	"ip_id" integer NOT NULL,
	"port" integer NOT NULL,
	"protocol_type" "protocoltype" NOT NULL,
	"detected_service_type" "detectedservicetype" NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "subchunks" (
	"id" serial PRIMARY KEY NOT NULL,
	"bot_snapshot_id" integer NOT NULL,
	"hash" varchar(32) NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ips" (
	"id" serial PRIMARY KEY NOT NULL,
	"ip" varchar NOT NULL,
	"last_ip_check_at" timestamp with time zone DEFAULT now() NOT NULL,
	"last_porter_check_at" timestamp with time zone DEFAULT now() NOT NULL,
	"country" varchar(2),
	"region" varchar(100),
	"city" varchar(100),
	"latitude" double precision,
	"longitude" double precision,
	"hostname" varchar(255),
	"asn" varchar(150),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"last_seen_at" timestamp with time zone DEFAULT now() NOT NULL,
	"is_multiport" boolean NOT NULL,
	CONSTRAINT "ips_ip_key" UNIQUE("ip")
);
--> statement-breakpoint
CREATE TABLE "servers" (
	"id" serial PRIMARY KEY NOT NULL,
	"port" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"is_lan" boolean NOT NULL,
	"server_type" "servertype" NOT NULL,
	"ip_id" integer NOT NULL,
	"last_bot_check_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "server_bot_snapshot_resource_pack_associations" (
	"bot_snapshot_id" integer NOT NULL,
	"resource_pack_id" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "server_bot_snapshot_resource_pack_associations_pkey" PRIMARY KEY("resource_pack_id","bot_snapshot_id")
);
--> statement-breakpoint
CREATE TABLE "server_snapshot_mod_associations" (
	"snapshot_id" integer NOT NULL,
	"mod_id" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "server_snapshot_mod_associations_pkey" PRIMARY KEY("snapshot_id","mod_id")
);
--> statement-breakpoint
CREATE TABLE "server_snapshot_plugin_associations" (
	"snapshot_id" integer NOT NULL,
	"plugin_id" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "server_snapshot_plugin_associations_pkey" PRIMARY KEY("snapshot_id","plugin_id")
);
--> statement-breakpoint
CREATE TABLE "server_bot_snapshot_mod_associations" (
	"bot_snapshot_id" integer NOT NULL,
	"mod_id" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "server_bot_snapshot_mod_associations_pkey" PRIMARY KEY("mod_id","bot_snapshot_id")
);
--> statement-breakpoint
ALTER TABLE "player_snapshots" ADD CONSTRAINT "player_snapshots_player_id_fkey" FOREIGN KEY ("player_id") REFERENCES "public"."players"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_bot_snapshots" ADD CONSTRAINT "server_bot_snapshots_server_id_fkey" FOREIGN KEY ("server_id") REFERENCES "public"."servers"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_dynamic_snapshots" ADD CONSTRAINT "server_dynamic_snapshots_server_id_fkey" FOREIGN KEY ("server_id") REFERENCES "public"."servers"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_sessions" ADD CONSTRAINT "server_sessions_server_id_fkey" FOREIGN KEY ("server_id") REFERENCES "public"."servers"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_snapshots" ADD CONSTRAINT "server_snapshots_server_id_fkey" FOREIGN KEY ("server_id") REFERENCES "public"."servers"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_snapshots" ADD CONSTRAINT "server_snapshots_software_id_fkey" FOREIGN KEY ("software_id") REFERENCES "public"."softwares"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "player_sessions" ADD CONSTRAINT "player_sessions_player_id_fkey" FOREIGN KEY ("player_id") REFERENCES "public"."players"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "player_sessions" ADD CONSTRAINT "player_sessions_server_id_fkey" FOREIGN KEY ("server_id") REFERENCES "public"."servers"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "ip_ports" ADD CONSTRAINT "ip_ports_ip_id_fkey" FOREIGN KEY ("ip_id") REFERENCES "public"."ips"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "subchunks" ADD CONSTRAINT "subchunks_bot_snapshot_id_fkey" FOREIGN KEY ("bot_snapshot_id") REFERENCES "public"."server_bot_snapshots"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "servers" ADD CONSTRAINT "servers_ip_id_fkey" FOREIGN KEY ("ip_id") REFERENCES "public"."ips"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_bot_snapshot_resource_pack_associations" ADD CONSTRAINT "server_bot_snapshot_resource_pack_associat_bot_snapshot_id_fkey" FOREIGN KEY ("bot_snapshot_id") REFERENCES "public"."server_bot_snapshots"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_bot_snapshot_resource_pack_associations" ADD CONSTRAINT "server_bot_snapshot_resource_pack_associa_resource_pack_id_fkey" FOREIGN KEY ("resource_pack_id") REFERENCES "public"."resource_packs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_snapshot_mod_associations" ADD CONSTRAINT "server_snapshot_mod_associations_mod_id_fkey" FOREIGN KEY ("mod_id") REFERENCES "public"."mods"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_snapshot_mod_associations" ADD CONSTRAINT "server_snapshot_mod_associations_server_snapshot_id_fkey" FOREIGN KEY ("snapshot_id") REFERENCES "public"."server_snapshots"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_snapshot_plugin_associations" ADD CONSTRAINT "server_snapshot_plugin_associations_plugin_id_fkey" FOREIGN KEY ("plugin_id") REFERENCES "public"."plugins"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_snapshot_plugin_associations" ADD CONSTRAINT "server_snapshot_plugin_associations_server_snapshot_id_fkey" FOREIGN KEY ("snapshot_id") REFERENCES "public"."server_snapshots"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_bot_snapshot_mod_associations" ADD CONSTRAINT "server_bot_snapshot_mod_associations_bot_snapshot_id_fkey" FOREIGN KEY ("bot_snapshot_id") REFERENCES "public"."server_bot_snapshots"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "server_bot_snapshot_mod_associations" ADD CONSTRAINT "server_bot_snapshot_mod_associations_mod_id_fkey" FOREIGN KEY ("mod_id") REFERENCES "public"."mods"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "ix_plugins_name" ON "plugins" USING btree ("name" text_ops);--> statement-breakpoint
CREATE INDEX "ix_players_created_at" ON "players" USING btree ("created_at" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "ix_players_player_type" ON "players" USING btree ("player_type" enum_ops);--> statement-breakpoint
CREATE INDEX "ix_player_snapshots_name" ON "player_snapshots" USING btree ("name" text_ops);--> statement-breakpoint
CREATE INDEX "ix_player_snapshots_player_id" ON "player_snapshots" USING btree ("player_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_player_snapshots_player_id_created_at" ON "player_snapshots" USING btree ("player_id" int4_ops,"created_at" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "ix_server_bot_snapshots_server_id" ON "server_bot_snapshots" USING btree ("server_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_bot_snapshots_server_id_created_at" ON "server_bot_snapshots" USING btree ("server_id" int4_ops,"created_at" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_dynamic_snapshots_players_online" ON "server_dynamic_snapshots" USING btree ("players_online" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_dynamic_snapshots_server_id" ON "server_dynamic_snapshots" USING btree ("server_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_dynamic_snapshots_server_id_created_at" ON "server_dynamic_snapshots" USING btree ("server_id" int4_ops,"created_at" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "ix_server_sessions_server_id" ON "server_sessions" USING btree ("server_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_sessions_server_id_from_desc" ON "server_sessions" USING btree ("server_id" int4_ops,"from_" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_mods_name" ON "mods" USING btree ("name" text_ops);--> statement-breakpoint
CREATE INDEX "ix_mods_name_version" ON "mods" USING btree ("name" text_ops,"version" text_ops);--> statement-breakpoint
CREATE INDEX "ix_server_snapshots_icon" ON "server_snapshots" USING btree ("icon" text_ops);--> statement-breakpoint
CREATE INDEX "ix_server_snapshots_players_max" ON "server_snapshots" USING btree ("players_max" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_snapshots_server_id" ON "server_snapshots" USING btree ("server_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_snapshots_server_id_created_at" ON "server_snapshots" USING btree ("server_id" timestamptz_ops,"created_at" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "ix_server_snapshots_software_id" ON "server_snapshots" USING btree ("software_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_server_snapshots_version" ON "server_snapshots" USING btree ("version" text_ops);--> statement-breakpoint
CREATE INDEX "ix_softwares_name" ON "softwares" USING btree ("name" enum_ops);--> statement-breakpoint
CREATE INDEX "ix_softwares_version" ON "softwares" USING btree ("version" text_ops);--> statement-breakpoint
CREATE INDEX "ix_player_sessions_player_id" ON "player_sessions" USING btree ("player_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_player_sessions_player_id_from_desc" ON "player_sessions" USING btree ("player_id" int4_ops,"from_" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "ix_player_sessions_server_id" ON "player_sessions" USING btree ("server_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_player_sessions_server_id_from_desc" ON "player_sessions" USING btree ("server_id" int4_ops,"from_" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "ix_ip_ports_detected_service_type" ON "ip_ports" USING btree ("detected_service_type" enum_ops);--> statement-breakpoint
CREATE INDEX "ix_ip_ports_ip_id" ON "ip_ports" USING btree ("ip_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_ip_ports_protocol_type_port" ON "ip_ports" USING btree ("protocol_type" int4_ops,"port" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_subchunks_bot_snapshot_id" ON "subchunks" USING btree ("bot_snapshot_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_subchunks_hash" ON "subchunks" USING btree ("hash" text_ops);--> statement-breakpoint
CREATE INDEX "ix_servers_created_at" ON "servers" USING btree ("created_at" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "ix_servers_ip_id" ON "servers" USING btree ("ip_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_servers_port" ON "servers" USING btree ("port" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_servers_server_type" ON "servers" USING btree ("server_type" enum_ops);--> statement-breakpoint
CREATE INDEX "ix_bot_rp_pack_id" ON "server_bot_snapshot_resource_pack_associations" USING btree ("resource_pack_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_bot_rp_snapshot_id" ON "server_bot_snapshot_resource_pack_associations" USING btree ("bot_snapshot_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_ss_mod_mod_id" ON "server_snapshot_mod_associations" USING btree ("mod_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_ss_mod_snapshot_id" ON "server_snapshot_mod_associations" USING btree ("snapshot_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_ss_plugin_plugin_id" ON "server_snapshot_plugin_associations" USING btree ("plugin_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_ss_plugin_snapshot_id" ON "server_snapshot_plugin_associations" USING btree ("snapshot_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_bot_mod_mod_id" ON "server_bot_snapshot_mod_associations" USING btree ("mod_id" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_bot_mod_snapshot_id" ON "server_bot_snapshot_mod_associations" USING btree ("bot_snapshot_id" int4_ops);
*/