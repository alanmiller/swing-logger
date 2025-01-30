CREATE TABLE shots (
    shot_key VARCHAR(36) PRIMARY KEY,
    round_key VARCHAR(36),
    player_key VARCHAR(36),
    player_name VARCHAR(100),
    shot_number INT,
    club_index INT,
    distance_to_pin FLOAT,
    total_distance FLOAT,
    
    -- Ball Data
    ball_speed FLOAT,
    total_spin FLOAT,
    back_spin FLOAT,
    side_spin FLOAT,
    hla FLOAT,  -- Horizontal Launch Angle
    vla FLOAT,  -- Vertical Launch Angle
    carry_distance FLOAT,
    offline FLOAT,
    decent_angle FLOAT,
    peak_height FLOAT,
    
    -- Club Data
    club_speed FLOAT,
    angle_of_attack FLOAT,
    face_to_target FLOAT,
    path FLOAT,
    
    -- Position Data
    start_x FLOAT,
    start_y FLOAT,
    start_z FLOAT,
    end_x FLOAT,
    end_y FLOAT,
    end_z FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);