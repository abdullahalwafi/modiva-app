# Hasil Evaluasi

## 4.3.2 Hasil Evaluasi ROUGE

Evaluasi ROUGE digunakan untuk mengukur kemiripan leksikal antara jawaban sistem dan jawaban referensi. Nilai yang digunakan meliputi precision, recall, dan F1 untuk ROUGE-1, ROUGE-2, dan ROUGE-L.

| Metrik | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| ROUGE-1 | 63.39% | 73.14% | 65.68% |
| ROUGE-2 | 57.45% | 66.45% | 59.18% |
| ROUGE-L | 62.70% | 71.95% | 64.82% |

## 4.3.3 Hasil Evaluasi BERTScore

Evaluasi BERTScore digunakan untuk mengukur kemiripan semantik antara jawaban sistem dan jawaban referensi. Nilai semantic similarity diambil dari skor BERTScore F1 karena F1 merepresentasikan keseimbangan antara precision dan recall berbasis embedding kontekstual.

| Metrik | Precision | Recall | F1 | Semantic Similarity |
| --- | ---: | ---: | ---: | ---: |
| BERTScore | 84.05% | 85.51% | 84.68% | 84.68% |

