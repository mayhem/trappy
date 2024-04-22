#include <stdint.h>

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

