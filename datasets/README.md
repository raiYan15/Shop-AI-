# Datasets

This project uses a product dataset for semantic search, recommendations, and RAG grounding.

## Included in repository

- `data/amazon.csv` (small curated runtime dataset)

## Original source

- Amazon products/reviews style dataset (Kaggle-style schema)
- If you want to replace it with a larger dataset, keep the same required columns (`product_id`, and either `title`/`description` or `product_name`/`about_product`).

## Recommended external source for larger experiments

- Kaggle: Amazon product/review datasets (choose a compatible schema)
- Keep large datasets out of GitHub and store under a local `data/` directory.

## Expected local structure

```text
Shop-AI-
├── data/
│   ├── amazon.csv
│   ├── faiss_index.idx            # generated (ignored)
│   ├── id_map.pkl                 # generated (ignored)
│   ├── faiss_live.idx             # generated (ignored)
│   └── id_map_live.pkl            # generated (ignored)
```

## Rebuild vectors/index after dataset update

```bash
python scripts/build_faiss.py
```
