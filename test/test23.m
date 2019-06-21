typedef uint64_t bkey_t;
typedef uint64_t clnt_id_t;
typedef uint64_t timestamp_t;
typedef uint8_t blob_t[512];

blob_t  get(clnt_id_t id, bkey_t key);

uint8_t put(clnt_id_t id, bkey_t key, blob_t blob);

uint8_t rem(clnt_id_t id, bkey_t key);
