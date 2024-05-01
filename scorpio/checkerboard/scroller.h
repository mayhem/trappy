#ifndef __SCROLLER_H__
#define __SCROLLER_H__

#include "defs.h"

const uint8_t INWARD = 0;
const uint8_t OUTWARD = 1;

void pattern_every_other(effect_t *eff, unsigned int row, color_t data[num_strips]);
void pattern_all(effect_t *eff, unsigned int row, color_t data[num_strips]);
void row_random(effect_t *eff, unsigned int index, color_t col[num_strips]);
void row_rainbow(effect_t *eff, unsigned int index, color_t col[num_strips]);
void row_binary(effect_t *eff, unsigned int index, color_t col[num_strips]);
void row_matrix(effect_t *eff, unsigned int index, color_t col[num_strips]);
void shift(effect_t *eff, unsigned int index, color_t buffer[total_leds], color_t *new_row, uint8_t direction);
unsigned int scroll(effect_t *eff, color_t buffer[total_leds], unsigned int row_index, int num_rows);

#endif
