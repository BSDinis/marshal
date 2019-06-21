#include <stdbool.h>

typedef bkey_t key;
typedef clnt_id_t key;
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

