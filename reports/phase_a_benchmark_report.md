# Phase A Benchmark Report

- dataset_root: `C:\Users\cubix\Desktop\성윤\samples_test`
- total_images: `30`

## DINO

- label_accuracy: `0.3667`
- category_accuracy: `0.1`
- avg_similarity: `0.7716`

| image | label | category | top_match_label | top_match_category | similarity |
|---|---|---|---|---|---|
| 01_portraits_01_REAL_portrait-woman.jpg | REAL | 01_portraits | AI | 07_products | 0.7507 |
| 01_portraits_02_AI_portrait-woman.jpg | AI | 01_portraits | REAL | 04_food | 0.6601 |
| 01_portraits_03_REAL_elderly-man.jpg | REAL | 01_portraits | REAL | 08_text_ocr | 0.8969 |
| 02_landscape_01_REAL_mountain-lake.jpg | REAL | 02_landscape | AI | 07_products | 0.7817 |
| 02_landscape_02_AI_mountain-sunset.jpg | AI | 02_landscape | AI | 10_illustration | 0.7984 |
| 02_landscape_03_REAL_ocean-beach.jpg | REAL | 02_landscape | AI | 10_illustration | 0.8332 |
| 03_animals_01_REAL_cat-closeup.jpg | REAL | 03_animals | REAL | 08_text_ocr | 0.8329 |
| 03_animals_02_AI_tiger-forest.jpg | AI | 03_animals | AI | 09_charts | 0.6366 |
| 03_animals_03_REAL_bird-branch.jpg | REAL | 03_animals | REAL | 08_text_ocr | 0.6920 |
| 04_food_01_REAL_food-plate.jpg | REAL | 04_food | AI | 07_products | 0.8145 |

## CLIP

- label_accuracy: `0.4667`
- category_accuracy: `0.0333`
- avg_similarity: `0.9046`

| image | label | category | top_match_label | top_match_category | similarity |
|---|---|---|---|---|---|
| 01_portraits_01_REAL_portrait-woman.jpg | REAL | 01_portraits | AI | 07_products | 0.9368 |
| 01_portraits_02_AI_portrait-woman.jpg | AI | 01_portraits | REAL | 04_food | 0.8420 |
| 01_portraits_03_REAL_elderly-man.jpg | REAL | 01_portraits | REAL | 08_text_ocr | 0.9693 |
| 02_landscape_01_REAL_mountain-lake.jpg | REAL | 02_landscape | REAL | 05_architecture | 0.8687 |
| 02_landscape_02_AI_mountain-sunset.jpg | AI | 02_landscape | REAL | 01_portraits | 0.9023 |
| 02_landscape_03_REAL_ocean-beach.jpg | REAL | 02_landscape | REAL | 08_text_ocr | 0.9123 |
| 03_animals_01_REAL_cat-closeup.jpg | REAL | 03_animals | REAL | 08_text_ocr | 0.9281 |
| 03_animals_02_AI_tiger-forest.jpg | AI | 03_animals | REAL | 08_text_ocr | 0.9042 |
| 03_animals_03_REAL_bird-branch.jpg | REAL | 03_animals | REAL | 08_text_ocr | 0.8709 |
| 04_food_01_REAL_food-plate.jpg | REAL | 04_food | AI | 07_products | 0.9642 |
