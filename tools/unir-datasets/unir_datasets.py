import os, pandas as pd, numpy as np

# Rutas relativas al proyecto para que funcione desde cualquier ubicación
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(PROJECT_DIR, 'datasets')
OUTPUT_DIR = DATA_DIR

def load_texts(base, ds, split):
    recs = []
    for lbl in ['pos', 'neg']:
        path = os.path.join(base, lbl)
        if not os.path.exists(path): continue
        for f in os.listdir(path):
            if f.endswith('.txt'):
                rating = int(f.split('_')[1][:-4]) if '_' in f else None
                with open(os.path.join(path, f), 'r', encoding='utf-8') as file:
                    recs.append({'texto': file.read().strip(), 'sentimiento': lbl, 'dataset': ds, 'split': split, 'rating': rating})
    return recs

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("SCRIPT: Unir Datasets (Simplificado)")
print("=" * 60)

# Cargar aclImdb y review_polarity
recs = load_texts(f"{DATA_DIR}/aclImdb_v1/aclImdb/train", 'aclImdb_v1', 'train') + \
       load_texts(f"{DATA_DIR}/aclImdb_v1/aclImdb/test", 'aclImdb_v1', 'test') + \
       load_texts(f"{DATA_DIR}/review_polarity/txt_sentoken", 'review_polarity', 'cv')
df = pd.DataFrame(recs)

# Cargar stanfordSST (Vectorizado)
sst = f"{DATA_DIR}/stanfordSentimentTreebank/stanfordSentimentTreebank"
if os.path.exists(sst):
    sent = pd.read_csv(f"{sst}/datasetSentences.txt", sep='\t', on_bad_lines='warn')
    labels = pd.read_csv(f"{sst}/sentiment_labels.txt", sep='|', on_bad_lines='warn')
    dic = pd.read_csv(f"{sst}/dictionary.txt", sep='|', on_bad_lines='warn')
    splits = pd.read_csv(f"{sst}/datasetSplit.txt", sep=',', on_bad_lines='warn')
    
    s = sent.merge(dic, left_on=sent.columns[1], right_on=dic.columns[0])
    s = s.merge(labels, left_on=dic.columns[1], right_on=labels.columns[0])
    s = s.merge(splits, on=splits.columns[0])
    
    s = s.rename(columns={sent.columns[1]: 'texto', labels.columns[1]: 'rating'})
    s['dataset'], s['sentiment_score'] = 'stanfordSST', s['rating']
    s['split'] = s[splits.columns[1]].map({1: 'train', 2: 'test', 3: 'dev'}).fillna('unknown')
    s['sentimiento'] = np.select([s['rating'] >= 0.6, s['rating'] <= 0.4], ['pos', 'neg'], 'neutral')
    
    df = pd.concat([df, s[['texto', 'sentimiento', 'dataset', 'split', 'rating', 'sentiment_score']]], ignore_index=True)

# Exportar
out = os.path.join(OUTPUT_DIR, 'dataset_unificado_bruto.csv')
df.to_csv(out, index=False)
print(f"Dataset guardado en: {out}")
print("=" * 60)