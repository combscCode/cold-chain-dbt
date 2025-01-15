{{ interval_detection(
    source_table=ref('stg_temperature_ts'),
    time_column='created_at',
    float_column='temperature',
    comparison_operator='>',
    threshold=8,
    duration_threshold=600
) }}
