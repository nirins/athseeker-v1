# Athena database for CloudFront logs
resource "aws_athena_database" "cloudfront_logs" {
  name   = "cloudfront_logs"
  bucket = aws_s3_bucket.cloudfront_logs.bucket
}

# Athena workgroup with results location
resource "aws_athena_workgroup" "cloudfront_logs" {
  name = "${var.project_name}-cloudfront-logs"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.cloudfront_logs.bucket}/athena-results/"
    }
  }
}

# CloudFront access logs table
resource "aws_athena_named_query" "create_table" {
  name      = "create-cloudfront-logs-table"
  workgroup = aws_athena_workgroup.cloudfront_logs.id
  database  = aws_athena_database.cloudfront_logs.name
  query     = <<-EOT
    CREATE EXTERNAL TABLE IF NOT EXISTS access_logs (
      `date`                      DATE,
      time                        STRING,
      x_edge_location             STRING,
      sc_bytes                    BIGINT,
      c_ip                        STRING,
      cs_method                   STRING,
      cs_host                     STRING,
      cs_uri_stem                 STRING,
      sc_status                   INT,
      cs_referer                  STRING,
      cs_user_agent               STRING,
      cs_uri_query                STRING,
      cs_cookie                   STRING,
      x_edge_result_type          STRING,
      x_edge_request_id           STRING,
      x_host_header               STRING,
      cs_protocol                 STRING,
      cs_bytes                    BIGINT,
      time_taken                  FLOAT,
      x_forwarded_for             STRING,
      ssl_protocol                STRING,
      ssl_cipher                  STRING,
      x_edge_response_result_type STRING,
      cs_protocol_version         STRING,
      fle_status                  STRING,
      fle_encrypted_fields        STRING,
      c_port                      INT,
      time_to_first_byte          FLOAT,
      x_edge_detailed_result_type STRING,
      sc_content_type             STRING,
      sc_content_len              BIGINT,
      sc_range_start              BIGINT,
      sc_range_end                BIGINT
    )
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    LOCATION 's3://${aws_s3_bucket.cloudfront_logs.bucket}/cloudfront/'
    TBLPROPERTIES ('skip.header.line.count' = '2');
  EOT
}

# Saved query: top IPs
resource "aws_athena_named_query" "top_ips" {
  name      = "top-ips-by-requests"
  workgroup = aws_athena_workgroup.cloudfront_logs.id
  database  = aws_athena_database.cloudfront_logs.name
  query     = <<-EOT
    SELECT c_ip, COUNT(*) AS requests
    FROM access_logs
    GROUP BY c_ip
    ORDER BY requests DESC
    LIMIT 20;
  EOT
}

# Saved query: search by IP
resource "aws_athena_named_query" "search_by_ip" {
  name      = "search-by-ip"
  workgroup = aws_athena_workgroup.cloudfront_logs.id
  database  = aws_athena_database.cloudfront_logs.name
  query     = <<-EOT
    SELECT date, time, c_ip, cs_uri_stem, sc_status, cs_user_agent
    FROM access_logs
    WHERE c_ip = '0.0.0.0'
    ORDER BY date DESC, time DESC;
  EOT
}
