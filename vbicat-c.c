#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const int BLOCKSIZE = (2048 * 32);

#define warn(...) \
    fprintf(stderr, __VA_ARGS__)
#define die(...) \
    do { warn(__VA_ARGS__); exit(1); } while (0)

#define PERIOD 10
int lines = PERIOD;
static const char CHARS[] = " .,oO0#";
#define BINS 64
int bins[BINS];
void update_histogram(const uint8_t buf[]) {
    ++lines;
    if (lines >= PERIOD) {
        int max = 0;
        for (int i = 0; i < BINS; i++) {
            if (bins[i] > max)
                max = bins[i];
        }
        if (max == 0)
            max = 1;

        const float scale = (sizeof(CHARS) - 2.0) / max;
        for (int i = 0; i < BINS; i++)
            warn("%c", CHARS[(int) (0.5 + (scale * bins[i]))]);
        warn("\n");

        lines = 0;
        for (int i = 0; i < BINS; i++)
            bins[i] = 0;
    }

    for (int i = 0; i < BLOCKSIZE; i++) {
        ++bins[buf[i] / (256 / BINS)];
    }
}

int main(int argc, char *argv[]) {
    if (argc != 2)
        die("Usage: vbicat2 VBIDEVICE >output.vbi\n");

    FILE *fin = fopen(argv[1], "rb");
    if (fin == NULL)
        die("Cannot open input file: %s\n", argv[1]);

    bool first = true;
    uint32_t prev_seq;
    int dropped = 0;
    uint8_t buf[BLOCKSIZE];
    while (true) {
        size_t rc = fread(buf, 1, BLOCKSIZE, fin);
        if (rc != BLOCKSIZE) {
            if (feof(fin))
                break;
            die("Read error");
        }

        uint32_t seq;
        memcpy(&seq, &buf[BLOCKSIZE - 4], sizeof seq);
        if (first) {
            first = false;
        } else if (seq != prev_seq + 1) {
            ++dropped;
            warn("Frame drop? %d\n", dropped);
        }
        prev_seq = seq;

        if (fwrite(buf, 1, BLOCKSIZE, stdout) != BLOCKSIZE)
            die("Write error");
        fflush(stdout);

        update_histogram(buf);
    }

    fclose(fin);

    return 0;
}
