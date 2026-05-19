# PCA Debug Report

Date: 2026-05-04

## Main Reason The PCA Is Not Clear

The PCA plot is unclear mostly because the document structure was not extracted correctly, and the visualization is too basic.

The source DOCX has all 376 paragraphs styled as `Normal`. The extractor in `backend/process_docx.py` expects Word heading styles such as `Heading 1`, `Heading 2`, or text starting with `#` / `##`. Because the DOCX does not use those styles, every chunk ended up under the same metadata:

- `section`: `Introduction`
- `chapter`: `Introduction générale`

That means the PCA cannot show meaningful groups by chapter or section. The text itself contains many real section titles like `Matériel & Méthodes`, `Results`, `Discussion`, and `Conclusion`, but they are treated as normal paragraph text.

## Evidence

- Number of chunks: `338`
- Unique chunks: `338`
- Median chunk length: `966.5` characters
- Mean chunk length: `814.1` characters
- Short chunks under 120 characters: `15`
- Chunks over 1000 characters: `156`
- Top section metadata: `Introduction` for all `338` chunks
- Top chapter metadata: `Introduction générale` for all `338` chunks
- PCA explained variance:
  - PC1: `10.10%`
  - PC2: `8.45%`
  - Total 2D variance: `18.55%`

## Secondary Causes

### PCA loses most semantic information

The embeddings are high-dimensional sentence-transformer vectors. Compressing them to only two PCA axes keeps only about `18.55%` of the variance. A scattered cloud is expected when 2D PCA is used on semantic embeddings.

### The visualization uses no labels or colors

`backend/vector_store.py` plots all points as the same blue dots:

```python
plt.scatter(pca_points[:, 0], pca_points[:, 1], alpha=0.5, c='blue', edgecolors='w', s=30)
```

There is no color by chapter, section, cluster, or topic. Even if clusters exist, the image does not explain them.

### Some chunks are only headings

There are 15 very short chunks, for example:

- `Prédiction générale de la théorie de la niche écologique`
- `Limites et développements de la théorie de la niche`
- `Matériel & Méthodes`
- `Results`
- `Conclusion`

These should usually be attached to the following paragraph instead of embedded as standalone chunks.

### Text encoding should be checked

Some terminal output showed mojibake like `Ã©`, `â€™`, and `Ã¨`. Reading the DOCX directly with Python shows correct French text, so this may be partly a PowerShell display issue. Still, the generated JSON should be inspected after regeneration to make sure text is stored correctly.

## Is It Text, Chunking, Or Something Else?

It is mainly chunking/extraction metadata, not the subject text.

The text is a scientific thesis-style corpus, so it naturally contains related ecological topics that may overlap semantically. That makes PCA less separated. But the bigger project problem is that the pipeline does not preserve document structure, so all chunks are treated as one big section.

The PCA method and static plot are the second problem. PCA is useful for a quick sanity check, but it is not a strong semantic map for sentence embeddings.

## Recommended Fixes

1. Fix heading detection in `backend/process_docx.py`.
   Since the DOCX uses only `Normal` style, detect title-like paragraphs by length, punctuation, casing, and known headings such as `Abstract`, `Introduction`, `Matériel & Méthodes`, `Results`, `Discussion`, `Conclusion`, `Chapitre`.

2. Do not keep heading-only chunks.
   Attach short headings to the next content chunk as metadata or prefix.

3. Add colors to the PCA plot.
   Color by detected chapter, detected section, or cluster label.

4. Add an alternative visualization.
   Use UMAP or t-SNE for a clearer 2D semantic layout, while keeping PCA as a diagnostic.

5. Add an interactive plot.
   A Plotly scatter with hover text showing `chunk_id`, section, and text preview will be much more useful than a static PNG.

## Files Checked

- `backend/process_docx.py`
- `backend/chunking.py`
- `backend/vector_store.py`
- `data/corpus_cleaned_fr.json`
- `data/corpus_chunks.json`
- `data/indexed_chunks.json`
- `data/pca_model.pkl`
- `data/pca_visualization.png`
