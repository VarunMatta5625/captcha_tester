# Input-variant experiment

Labels: v4 reads with confidence >= 0.7 (93,185 non-gold captchas), 70/20/10 train/test/val, same split for
every run. From scratch, 10 epochs max, best-val epoch kept. Gold = your 200 checked captchas (scored only).

v4 (teacher) on gold: 93.5%

| run | best epoch | val | test | gold | gold, best epoch of the 10 | gold, mean of epochs 3-10 |
|---|---|---|---|---|---|---|
| binary_s0 | 10 | 99.45% | 99.44% | 95.0% | 96.5% | 95.2% |
| binary_s0_init-v4 | 1 | 99.76% | 99.73% | 93.5% | 94.5% | 94.5% |
| binary_s1 | 10 | 99.41% | 99.40% | 95.0% | 97.0% | 95.7% |
| raw_s0 | 8 | 98.66% | 98.84% | 95.5% | 99.0% | 96.7% |
| raw_s1 | 9 | 98.73% | 98.93% | 96.5% | 98.0% | 95.8% |
| three_s0 | 10 | 99.06% | 99.17% | 97.0% | 98.5% | 97.1% |
| three_s0_init-v4 | 4 | 98.84% | 98.97% | 96.0% | 97.5% | 96.6% |
| three_s1 | 10 | 99.08% | 99.14% | 96.0% | 99.0% | 96.8% |

## Per variant (mean over seeds)

| variant | seeds | val | gold | gold, mean of epochs 3-10 | gold misses (union over seeds) |
|---|---|---|---|---|---|
| binary | 3 | 99.54% | 94.5% | 95.3% | 13 |
| raw | 2 | 98.70% | 96.0% | 96.3% | 9 |
| three | 3 | 98.99% | 96.3% | 96.9% | 10 |

## Gold confusions (true -> read), summed over seeds

- **binary**: 6->5 x15, J->3 x9, 3->J x3, B->8 x3, b->h x3
- **raw**: 6->5 x7, J->3 x4, 3->J x2, B->8 x2, b->h x1
- **three**: 6->5 x11, J->3 x6, 3->J x3, B->8 x3
- **v4 (teacher)**: 6->5 x5, J->3 x3, y->Y x2, 8->B x1, 3->J x1, B->8 x1, b->h x1

## Every gold captcha any run gets wrong

| id | truth | v4 | binary_s0 | binary_s0_init-v4 | binary_s1 | raw_s0 | raw_s1 | three_s0 | three_s0_init-v4 | three_s1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 150 | J2qgj | 32qgj | ok | 32qgj | ok | 32qgj | 32qgj | 32qgj | ok | 32qgj |
| 8152 | yB4AJ | YB4AJ | ok | ok | ok | ok | ok | ok | ok | ok |
| 9699 | RAb6N | RAb5N | RAb5N | RAb5N | RAb5N | RAb5N | RAb5N | RAb5N | RAb5N | RAb5N |
| 13304 | J4RyN | 34RYN | ok | 34RyN | ok | ok | ok | ok | ok | 34RyN |
| 15120 | nGDJ3 | ok | ok | nGD33 | nGD33 | ok | ok | ok | ok | ok |
| 18255 | mM8Ld | mMBLd | ok | ok | ok | ok | ok | ok | ok | ok |
| 19263 | hy342 | hyJ42 | hyJ42 | hyJ42 | hyJ42 | hyJ42 | hyJ42 | hyJ42 | hyJ42 | hyJ42 |
| 43665 | Dy6ie | Dy5ie | Dy5ie | Dy5ie | Dy5ie | Dy5ie | Dy5ie | Dy5ie | Dy5ie | Dy5ie |
| 58025 | 2iJFm | 2i3Fm | 2i3Fm | 2i3Fm | ok | 2i3Fm | 2i3Fm | ok | 2i3Fm | 2i3Fm |
| 70817 | bAJ9G | ok | bA39G | bA39G | bA39G | ok | ok | ok | ok | ok |
| 71755 | m6t2J | m5t2J | m5t2J | m5t2J | m5t2J | m5t2J | m5t2J | ok | m5t23 | ok |
| 72421 | NMFb6 | NMFb5 | NMFb5 | NMFb5 | NMFb5 | NMFb5 | ok | NMFb5 | NMFb5 | NMFb5 |
| 79474 | j4rMB | j4rM8 | j4rM8 | j4rM8 | j4rM8 | j4rM8 | j4rM8 | j4rM8 | j4rM8 | j4rM8 |
| 83942 | D6TnY | D5TnY | D5TnY | D5TnY | D5TnY | ok | ok | ok | D5TnY | ok |
| 95310 | 3DbLA | 3DhLA | 3DhLA | 3DhLA | 3DhLA | 3DhLA | ok | ok | ok | ok |

## Ensembles on gold (mean of softmax over that variant's seeds)

- binary (3 models): 95.0%
- raw (2 models): 96.0%
- three (3 models): 96.5%

## The 8 captchas the live site rejected (truth = Claude's reading, unchecked)

- v4: 6/8  3nJTr JMba5 JAhJ3 J8NNt gjt9J Y8y9N 5g8Nf 8Lar3
- binary_s0: 6/8  3nJTr JMba5 JAhJ3 J8NNt gjt9J Y8y9N 5g8Nf 8Lar3
- binary_s0_init-v4: 5/8  3nJTr JMba5 JAh33 J8NNt gjt9J Y8y9N 5g8Nf 8Lar3
- binary_s1: 5/8  3nJTr JMba5 JAh33 J8NNt gjt9J Y8y9N 5g8Nf 8Lar3
- raw_s0: 5/8  3nJTr JMba5 JAhJ3 J8NNt gjt93 Y8y9N 5g8Nf 8Lar3
- raw_s1: 5/8  3nJTr JMba5 JAhJ3 J8NNt gjt93 Y8y9N 5g8Nf 8Lar3
- three_s0: 6/8  3nJTr JMba5 JAhJ3 J8NNt gjt9J Y8y9N 5g8Nf 8Lar3
- three_s0_init-v4: 6/8  3nJTr JMba5 JAhJ3 J8NNt gjt9J Y8y9N 5g8Nf 8Lar3
- three_s1: 7/8  3nJTr JMbe5 JAhJ3 J8NNt gjt9J Y8y9N 5g8Nf 8Lar3
