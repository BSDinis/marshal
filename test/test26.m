/**
 * dev.m
 *
 * Marshal interface specifications
 *
 *   device - device
 */

#include <stdbool.h>

typedef struct metadata
{
  uint8_t 	enc_key[32];
  uint8_t 	enc_iv[16];
  uint8_t 	enc_data_hash[32];
  uint64_t 	pol_id;
  char	  	ustor_name[424];
} blob_t;

// write_response
// since there are no unions nor optional returns,
// this econmpasses everything
//
// (this is the same for rems)
// plz FIXME
struct write_resp {
  bool ack;
  blob_t blob;
  uint64_t ts;
};

struct timestamped_blob_t {
  blob_t blob;
  uint64_t ts;
};

// get
timestamped_blob_t get(uint64_t key);

// put
write_resp put(uint64_t key, uint64_t ts, blob_t blob);

// rem
write_resp rem(uint64_t key, uint64_t ts);

