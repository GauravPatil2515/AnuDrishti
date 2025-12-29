-- Supabase Database Schema for DrugTox-AI Platform
-- Run these SQL commands in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create predictions table
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    smiles TEXT NOT NULL,
    molecule_name TEXT,
    endpoints JSONB NOT NULL,
    ai_analysis TEXT,
    user_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    -- Indexes for better performance
    CONSTRAINT valid_smiles CHECK (length(smiles) > 0)
);

-- Create indexes
CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX idx_predictions_smiles ON predictions(smiles);

-- Create user feedback table
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    user_id TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    is_accurate BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create molecule library table
CREATE TABLE molecule_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    smiles TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    known_toxicity JSONB,
    drug_bank_id TEXT,
    cas_number TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_name CHECK (length(name) > 0),
    CONSTRAINT valid_category CHECK (length(category) > 0)
);

-- Create indexes for molecule library
CREATE INDEX idx_molecule_library_category ON molecule_library(category);
CREATE INDEX idx_molecule_library_name ON molecule_library(name);
CREATE INDEX idx_molecule_library_smiles ON molecule_library(smiles);

-- Create analytics/stats view
CREATE VIEW prediction_analytics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_predictions,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(CASE 
        WHEN endpoints->>'NR-AR-LBD' = 'Toxic' THEN 1 
        ELSE 0 
    END) as toxicity_rate
FROM predictions
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Insert sample molecules into library
INSERT INTO molecule_library (name, smiles, category, description, known_toxicity) VALUES
('Caffeine', 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', 'stimulant', 'Central nervous system stimulant', '{"generally_safe": true, "ld50": "192 mg/kg"}'),
('Aspirin', 'CC(=O)OC1=CC=CC=C1C(=O)O', 'nsaid', 'Non-steroidal anti-inflammatory drug', '{"generally_safe": true, "gastrointestinal_risk": "moderate"}'),
('Ibuprofen', 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O', 'nsaid', 'Non-steroidal anti-inflammatory drug', '{"generally_safe": true, "cardiovascular_risk": "low"}'),
('Benzene', 'C1=CC=CC=C1', 'solvent', 'Industrial solvent, known carcinogen', '{"carcinogenic": true, "highly_toxic": true}'),
('Ethanol', 'CCO', 'alcohol', 'Ethyl alcohol, beverage alcohol', '{"moderate_toxicity": true, "hepatotoxic": "chronic_use"}'),
('Acetaminophen', 'CC(=O)NC1=CC=C(C=C1)O', 'analgesic', 'Pain reliever and fever reducer', '{"hepatotoxic": "overdose", "generally_safe": "therapeutic_doses"}'),
('Morphine', 'CN1CC[C@]23C4=C5C=CC(=C4[C@H]1[C@H]2[C@H](C3)O)O[C@H]5O', 'opioid', 'Opioid pain medication', '{"addictive": true, "respiratory_depression": true}'),
('Warfarin', 'CC(=O)CC(C1=CC=CC=C1)C2=C(C3=CC=CC=C3OC2=O)O', 'anticoagulant', 'Blood thinner medication', '{"hemorrhage_risk": true, "teratogenic": true}'),
('Metformin', 'CN(C)C(=N)N=C(N)N', 'antidiabetic', 'Type 2 diabetes medication', '{"generally_safe": true, "lactic_acidosis": "rare"}'),
('Penicillin G', 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C', 'antibiotic', 'Beta-lactam antibiotic', '{"allergic_reactions": "possible", "generally_safe": true}');

-- Row Level Security (RLS) policies
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE molecule_library ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for demo (adjust for production)
CREATE POLICY "Allow anonymous access to predictions" ON predictions
    FOR ALL USING (true);

CREATE POLICY "Allow anonymous access to user_feedback" ON user_feedback
    FOR ALL USING (true);

CREATE POLICY "Allow read access to molecule_library" ON molecule_library
    FOR SELECT USING (true);

-- Functions for common operations

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_stats(user_id_param TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_predictions', COUNT(*),
        'toxic_predictions', COUNT(*) FILTER (WHERE endpoints->>'overall' = 'Toxic'),
        'safe_predictions', COUNT(*) FILTER (WHERE endpoints->>'overall' = 'Safe'),
        'avg_confidence', AVG((endpoints->>'confidence')::FLOAT),
        'last_prediction', MAX(created_at)
    ) INTO result
    FROM predictions 
    WHERE user_id = user_id_param;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to search molecules by similarity (placeholder for future implementation)
CREATE OR REPLACE FUNCTION search_similar_molecules(target_smiles TEXT, limit_count INTEGER DEFAULT 10)
RETURNS TABLE(
    id UUID,
    name TEXT,
    smiles TEXT,
    category TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    -- Simple text similarity for now - replace with chemical similarity in production
    RETURN QUERY
    SELECT 
        ml.id,
        ml.name,
        ml.smiles,
        ml.category,
        (CASE 
            WHEN ml.smiles = target_smiles THEN 1.0
            WHEN ml.smiles ILIKE '%' || target_smiles || '%' THEN 0.8
            ELSE similarity(ml.smiles, target_smiles)
        END) as similarity_score
    FROM molecule_library ml
    ORDER BY similarity_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Create notification function for real-time updates
CREATE OR REPLACE FUNCTION notify_prediction_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('prediction_created', NEW.id::TEXT);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for notifications
CREATE TRIGGER prediction_created_trigger
    AFTER INSERT ON predictions
    FOR EACH ROW
    EXECUTE FUNCTION notify_prediction_created();

-- Comments for documentation
COMMENT ON TABLE predictions IS 'Stores toxicity prediction results with AI analysis';
COMMENT ON TABLE user_feedback IS 'Stores user feedback on prediction accuracy';
COMMENT ON TABLE molecule_library IS 'Library of known molecules with toxicity information';
COMMENT ON VIEW prediction_analytics IS 'Analytics view for prediction statistics';