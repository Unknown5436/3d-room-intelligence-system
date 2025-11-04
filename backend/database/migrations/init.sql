-- Database initialization script
-- Section C3: PostgreSQL + PostGIS + Pointcloud Extension setup

-- Enable spatial extensions
CREATE EXTENSION IF NOT EXISTS postgis;
-- Note: pointcloud extension is optional and may not be available in all PostGIS images
-- If needed, use a custom Docker image with pointcloud support
-- CREATE EXTENSION IF NOT EXISTS pointcloud;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verify installation (can be run manually)
-- SELECT PostGIS_Version();
-- SELECT PC_Version();

-- Table: rooms (Primary room metadata)
-- Hybrid approach combining dimension storage with metadata
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    point_count INTEGER,
    processed_points INTEGER,
    length FLOAT,
    width FLOAT,
    height FLOAT,
    accuracy VARCHAR(50),
    scan_quality FLOAT CHECK (scan_quality BETWEEN 0 AND 1),
    extra_metadata JSONB DEFAULT '{}'::jsonb
);

-- Table: point_cloud_patches (Point cloud storage)
-- Note: PCPATCH type requires pointcloud extension (optional)
-- For now, using TEXT to store point cloud data as JSON or base64
CREATE TABLE IF NOT EXISTS point_cloud_patches (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    patch TEXT,  -- Changed from PCPATCH(1) to TEXT for compatibility
    envelope GEOMETRY(POLYGON, 4326),
    patch_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index on point cloud patches (Section C3)
-- Note: PC_EnvelopeGeometry requires pointcloud extension
-- Using envelope geometry index instead
CREATE INDEX IF NOT EXISTS room_patches_envelope_idx 
ON point_cloud_patches USING GIST(envelope);

-- Table: detected_objects (Furniture/object detection results)
-- Comprehensive approach with geometric and safety fields
CREATE TABLE IF NOT EXISTS detected_objects (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    object_type VARCHAR(50),
    position GEOMETRY(PointZ, 4326),
    dimensions JSONB,
    volume FLOAT,
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    classification_method VARCHAR(20),
    extra_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index on detected objects (Section C3)
CREATE INDEX IF NOT EXISTS objects_spatial_idx 
ON detected_objects USING GIST(position);

CREATE INDEX IF NOT EXISTS objects_room_id_idx 
ON detected_objects(room_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
