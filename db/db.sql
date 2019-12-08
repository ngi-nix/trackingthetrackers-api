CREATE DATABASE bincache;

\c bincache

CREATE TABLE "cache" (
    filename varchar(500),      -- file name on disk
    md5 varchar(33), 
    sha1 varchar(42), 
    sha256 varchar(65) primary key, 
    first_seen timestamp with time zone, 
    analyzed_at timestamp with time zone
);


CREATE index idx_cache_sha256 on "cache"(sha256);

