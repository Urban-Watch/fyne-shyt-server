-- Database Migration Script: Add AI Analysis Fields
-- Run this SQL in your Supabase SQL editor to add the missing columns

-- Add severity_score column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'severity_score') THEN
        ALTER TABLE reports ADD COLUMN severity_score INTEGER CHECK (severity_score >= 1 AND severity_score <= 1000);
    END IF;
END $$;

-- Add severity_analysis column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'severity_analysis') THEN
        ALTER TABLE reports ADD COLUMN severity_analysis TEXT;
    END IF;
END $$;

-- Add impact_score column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'impact_score') THEN
        ALTER TABLE reports ADD COLUMN impact_score INTEGER CHECK (impact_score >= 1 AND impact_score <= 100);
    END IF;
END $$;

-- Add impact_analysis column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'impact_analysis') THEN
        ALTER TABLE reports ADD COLUMN impact_analysis TEXT;
    END IF;
END $$;

-- Add population_estimate column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'population_estimate') THEN
        ALTER TABLE reports ADD COLUMN population_estimate INTEGER;
    END IF;
END $$;

-- Add vehicle_estimate column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'vehicle_estimate') THEN
        ALTER TABLE reports ADD COLUMN vehicle_estimate INTEGER;
    END IF;
END $$;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'reports'
AND column_name IN ('severity_score', 'severity_analysis', 'impact_score', 'impact_analysis', 'population_estimate', 'vehicle_estimate')
ORDER BY column_name;
