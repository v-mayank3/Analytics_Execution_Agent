-- Bronze table DDL generated from inferred schema

CREATE TABLE electricity_interval (
    Timestamp DATETIME2,
    SiteID NVARCHAR(4000),
    Units INT,
    Region NVARCHAR(4000),
    _source_file NVARCHAR(500),
    _ingestion_timestamp DATETIME2
);

CREATE TABLE mobile_traffic (
    Timestamp DATETIME2,
    DeviceID NVARCHAR(4000),
    UsageMB DECIMAL(18,2),
    Region NVARCHAR(4000),
    _source_file NVARCHAR(500),
    _ingestion_timestamp DATETIME2
);

CREATE TABLE solar_bronze (
    Timestamp DATETIME2,
    PlantID NVARCHAR(4000),
    Generation INT,
    _source_file NVARCHAR(500),
    _ingestion_timestamp DATETIME2
);
