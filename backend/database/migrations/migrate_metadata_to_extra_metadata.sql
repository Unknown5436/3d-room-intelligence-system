-- Migration script: Rename 'metadata' to 'extra_metadata' in rooms and detected_objects tables
-- Run this if you have an existing database with the old 'metadata' column name

-- For rooms table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rooms' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE rooms RENAME COLUMN metadata TO extra_metadata;
        RAISE NOTICE 'Renamed metadata to extra_metadata in rooms table';
    ELSE
        RAISE NOTICE 'rooms.metadata column does not exist (may already be migrated)';
    END IF;
END $$;

-- For detected_objects table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'detected_objects' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE detected_objects RENAME COLUMN metadata TO extra_metadata;
        RAISE NOTICE 'Renamed metadata to extra_metadata in detected_objects table';
    ELSE
        RAISE NOTICE 'detected_objects.metadata column does not exist (may already be migrated)';
    END IF;
END $$;


