-- Database Migration: Add Individual Score Fields
-- Run this SQL in your Supabase SQL editor to add the new columns to existing reports table

-- Add new columns for individual scores and analyses
ALTER TABLE reports 
ADD COLUMN IF NOT EXISTS severity_score INTEGER CHECK (severity_score >= 1 AND severity_score <= 1000),
ADD COLUMN IF NOT EXISTS severity_analysis TEXT,
ADD COLUMN IF NOT EXISTS impact_score INTEGER CHECK (impact_score >= 1 AND impact_score <= 100),
ADD COLUMN IF NOT EXISTS impact_analysis TEXT,
ADD COLUMN IF NOT EXISTS population_estimate INTEGER,
ADD COLUMN IF NOT EXISTS vehicle_estimate INTEGER;

-- Update any existing NULL values to have default values (optional)
-- You can run this if you want to set defaults for existing records
-- UPDATE reports 
-- SET 
--     severity_score = CASE WHEN severity_score IS NULL THEN 1 ELSE severity_score END,
--     impact_score = CASE WHEN impact_score IS NULL THEN 1 ELSE impact_score END,
--     population_estimate = CASE WHEN population_estimate IS NULL THEN 0 ELSE population_estimate END,
--     vehicle_estimate = CASE WHEN vehicle_estimate IS NULL THEN 0 ELSE vehicle_estimate END
-- WHERE severity_score IS NULL OR impact_score IS NULL OR population_estimate IS NULL OR vehicle_estimate IS NULL;

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'reports' 
ORDER BY ordinal_position;
