#ifndef __DEFS_H__
#define __DEFS_H__

#include <stdint.h>

const uint16_t num_leds = 144;
const uint16_t num_strips = 8;
const uint16_t total_leds = num_leds * num_strips;
const uint16_t total_leds_bytes = total_leds * 3;
const uint16_t bytes_per_row = num_strips * 3;

#define min(a,b)  (((a) < (b)) ? (a) : (b))

typedef struct  {
    uint8_t red, green, blue;
} color_t;

typedef struct {
    float   index;
    color_t color;
} palette_t;

typedef struct {
    palette_t palette[16];
    uint8_t   points;
    uint8_t   leds;
} gradient_t;

typedef struct effect_t {
    gradient_t  palette;
    void      (*pattern_fptr)(effect_t *, unsigned int row, color_t[num_strips]);
    void      (*row_fptr)(effect_t *, unsigned int row, color_t[num_strips]);
} effect_t;

#endif
