#include <stdbool.h>

typedef uint64_t bkey_t;
typedef uint64_t clnt_id_t;
typedef uint64_t timestamp_t;
typedef uint8_t blob_t[512];


struct write_resp {
  bool ack;
  blob_t blob;
  timestamp_t ts;
};

struct timestamped_blob_t {
  blob_t blob;
  timestamp_t ts;
};

timestamped_blob_t get(bkey_t key);

write_resp put(bkey_t key, timestamp_t ts, blob_t blob);

write_resp rem(bkey_t key, timestamp_t ts);

