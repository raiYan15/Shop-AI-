import argparse
import os
import pickle
import pandas as pd
import numpy as np
from tqdm import tqdm

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    raise SystemExit('Install sentence-transformers: pip install sentence-transformers')

try:
    import faiss
except Exception:
    raise SystemExit('Install faiss-cpu: pip install faiss-cpu')

from sklearn.preprocessing import normalize


def load_products(path, nrows=None):
    df = pd.read_csv(path, nrows=nrows)
    # Handle both formats: title/description or product_name/about_product
    if 'title' not in df.columns and 'product_name' not in df.columns:
        raise ValueError("CSV must have either 'title' or 'product_name' column")
    if 'product_id' not in df.columns:
        raise ValueError("CSV must have 'product_id' column")
    
    df = df.fillna('')
    # Drop duplicate rows based on product_id
    df = df.drop_duplicates(subset=['product_id'], keep='first')
    
    title_col = 'title' if 'title' in df.columns else 'product_name'
    desc_col = 'description' if 'description' in df.columns else 'about_product'
    
    df['text'] = df[title_col].astype(str) + '. ' + df[desc_col].astype(str)
    return df[['product_id', 'text']].reset_index(drop=True)


def build_embeddings(texts, model_name='all-mpnet-base-v2', batch_size=64):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype('float32')
    # normalize for cosine similarity with inner product
    embeddings = normalize(embeddings)
    return embeddings


def build_faiss_index(embeddings, index_path):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, index_path)


def save_id_map(ids, path):
    with open(path, 'wb') as f:
        pickle.dump(list(ids), f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--products', required=True, help='CSV path for products')
    parser.add_argument('--nrows', type=int, default=None)
    parser.add_argument('--model', default='all-mpnet-base-v2')
    parser.add_argument('--index-out', default='faiss_index.idx')
    parser.add_argument('--idmap-out', default='id_map.pkl')
    args = parser.parse_args()

    df = load_products(args.products, nrows=args.nrows)
    texts = df['text'].tolist()
    product_ids = df['product_id'].tolist()
    print(f'Computing embeddings for {len(texts)} products using {args.model}...')
    embeddings = build_embeddings(texts, model_name=args.model)

    print(f'Building FAISS index (dim={embeddings.shape[1]}) and saving to {args.index_out}...')
    build_faiss_index(embeddings, args.index_out)

    print(f'Saving id map to {args.idmap_out}...')
    save_id_map(product_ids, args.idmap_out)

    print(f'✓ Done. Index built for {len(product_ids)} products.')


if __name__ == "__main__":
    main()
