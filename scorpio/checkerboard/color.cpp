#include <stdlib.h>

#include "color.h"

void random_color(color_t *col)
{
    col->red = rand() % 128 + 127;
    col->green = rand() % 128 + 127;
    col->blue = rand() % 128 + 127;
}
