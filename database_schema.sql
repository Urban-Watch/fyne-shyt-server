-- Urban Watch Database Schema for Supabase
-- Run this SQL in your Supabase SQL editor to create the required tables

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    mobile_no VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on mobile_no for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_mobile_no ON users(mobile_no);

-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
    report_id VARCHAR(255) PRIMARY KEY,
    user_ids TEXT[] NOT NULL DEFAULT '{}',
    people_reported INTEGER NOT NULL DEFAULT 1,
    category VARCHAR(50) NOT NULL CHECK (category IN ('potholes', 'trash_overflow')),
    title VARCHAR(200) NOT NULL,
    ai_analysis TEXT,
    images TEXT[] NOT NULL DEFAULT '{}',
    location JSONB NOT NULL,
    criticality_score INTEGER NOT NULL CHECK (criticality_score >= 1 AND criticality_score <= 100),
    status VARCHAR(50) NOT NULL DEFAULT 'waiting_for_attention' CHECK (status IN ('waiting_for_attention', 'got_the_attention', 'resolved')),
    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_criticality_score ON reports(criticality_score);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_reports_user_ids ON reports USING GIN (user_ids);

-- Create index for location queries (using GIN index on JSONB)
CREATE INDEX IF NOT EXISTS idx_reports_location ON reports USING GIN (location);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at 
    BEFORE UPDATE ON reports 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for better security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
-- Users can only see and modify their own data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Create policies for reports table
-- Users can view reports they are part of
CREATE POLICY "Users can view own reports" ON reports
    FOR SELECT USING (auth.uid()::text = ANY(user_ids));

-- Users can insert new reports
CREATE POLICY "Users can create reports" ON reports
    FOR INSERT WITH CHECK (auth.uid()::text = ANY(user_ids));

-- Service role can do everything (for admin operations)
CREATE POLICY "Service role can do everything on users" ON users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything on reports" ON reports
    FOR ALL USING (auth.role() = 'service_role');

-- Sample data (optional - remove in production)
-- INSERT INTO users (user_id, mobile_no, name, address) VALUES
-- ('admin_user_123', '1234567890', 'Admin User', 'Admin Address'),
-- ('test_user_456', '9876543210', 'Test User', 'Test Address');
