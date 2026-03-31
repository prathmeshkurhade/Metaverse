-- ============================================================
-- SUPABASE DATABASE SCHEMA FOR 2D METAVERSE
-- ============================================================
-- Run this in your Supabase SQL Editor (Dashboard -> SQL Editor -> New Query)
--
-- WHY SQL instead of an ORM migration?
-- Supabase IS PostgreSQL. You write SQL directly. No SQLAlchemy, no Prisma,
-- no migration files. This is actually simpler for a Supabase project.
-- In a traditional PostgreSQL setup, you'd use Alembic (Python) for migrations.
--
-- TABLE RELATIONSHIPS:
-- users 1->N spaces (a user creates many spaces)
-- users 1->1 user_metadata (a user has one avatar selection)
-- avatars 1->N user_metadata (many users can pick the same avatar)
-- maps 1->N map_elements (a map template has many default elements)
-- maps 1->N spaces (many spaces can be created from the same map)
-- elements 1->N map_elements (an element can appear in many maps)
-- elements 1->N space_elements (an element can be placed in many spaces)
-- spaces 1->N space_elements (a space has many placed elements)
-- spaces 1->N room_messages (a space has many chat messages)
-- ============================================================

-- ─── Enable UUID extension ───
-- WHY? PostgreSQL doesn't generate UUIDs by default. This extension adds
-- the gen_random_uuid() function used in our primary keys.
-- UUIDs vs auto-increment IDs: UUIDs are globally unique (no collisions
-- across tables or databases). Auto-increment leaks info (user count).
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Users Table ───
-- Stores account information. Password is bcrypt-hashed (never plain text).
-- WHY UUID for id? So user IDs can be embedded in JWTs and URLs without
-- being guessable. Auto-increment (1, 2, 3...) would let attackers enumerate users.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,  -- bcrypt hash, NOT plain text
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Avatars Table ───
-- Available avatars that users can select. Created by admins.
-- WHY serial ID? Avatars are created by admins and referenced by ID.
-- Sequential IDs are fine here -- no security concern about knowing
-- there are 10 avatars. Also simpler for the test spec which uses numeric IDs.
CREATE TABLE IF NOT EXISTS avatars (
    id SERIAL PRIMARY KEY,
    image_url TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Elements Table ───
-- Reusable assets (trees, buildings, etc.) that can be placed in spaces.
-- WHY separate from space_elements? An element is a TYPE (e.g., "Oak Tree").
-- A space_element is an INSTANCE (e.g., "Oak Tree at position (5, 10) in Room A").
-- This avoids storing image_url 100 times if one tree is placed 100 times.
CREATE TABLE IF NOT EXISTS elements (
    id SERIAL PRIMARY KEY,
    image_url TEXT NOT NULL,
    width INTEGER NOT NULL DEFAULT 1,
    height INTEGER NOT NULL DEFAULT 1,
    static BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Maps Table ───
-- Templates for spaces. Defines dimensions and default element placements.
-- WHY maps? So admins can create room templates that users can instantiate.
-- Without maps, every user would start with an empty room.
CREATE TABLE IF NOT EXISTS maps (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    thumbnail TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Map Elements Table ───
-- Default element placements for a map template.
-- When a user creates a space from this map, these elements get COPIED
-- into the space_elements table (they're not shared references).
CREATE TABLE IF NOT EXISTS map_elements (
    id SERIAL PRIMARY KEY,
    map_id INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
    element_id INTEGER NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL
);

-- ─── Spaces Table ───
-- Rooms in the metaverse. Created by users, optionally from a map template.
-- WHY UUID for id? Same reason as users -- spaces are referenced in URLs
-- and WebSocket messages. UUIDs prevent guessing.
CREATE TABLE IF NOT EXISTS spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    map_id INTEGER REFERENCES maps(id) ON DELETE SET NULL,
    thumbnail TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Space Elements Table ───
-- Element instances placed in a specific space at a specific position.
-- Each row = one element placed at (x, y) in a room.
CREATE TABLE IF NOT EXISTS space_elements (
    id SERIAL PRIMARY KEY,
    space_id UUID NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
    element_id INTEGER NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL
);

-- ─── User Metadata Table ───
-- Maps users to their selected avatar. One avatar per user.
-- WHY ON CONFLICT? When a user changes their avatar, we upsert (update if exists).
CREATE TABLE IF NOT EXISTS user_metadata (
    id SERIAL PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    avatar_id INTEGER NOT NULL REFERENCES avatars(id) ON DELETE CASCADE
);

-- ─── Room Messages Table ───
-- Chat history for the AI Room Assistant.
-- Each message is either from a "user" or the "assistant" (Claude).
CREATE TABLE IF NOT EXISTS room_messages (
    id SERIAL PRIMARY KEY,
    space_id UUID NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL for AI messages
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Indexes ───
-- WHY indexes? Without them, queries like "find all spaces by creator_id"
-- would scan EVERY row in the table (full table scan). With an index,
-- PostgreSQL jumps directly to matching rows. Think of it like a book index
-- vs reading every page to find a topic.
CREATE INDEX IF NOT EXISTS idx_spaces_creator ON spaces(creator_id);
CREATE INDEX IF NOT EXISTS idx_space_elements_space ON space_elements(space_id);
CREATE INDEX IF NOT EXISTS idx_map_elements_map ON map_elements(map_id);
CREATE INDEX IF NOT EXISTS idx_user_metadata_user ON user_metadata(user_id);
CREATE INDEX IF NOT EXISTS idx_room_messages_space ON room_messages(space_id);
CREATE INDEX IF NOT EXISTS idx_room_messages_created ON room_messages(space_id, created_at);
