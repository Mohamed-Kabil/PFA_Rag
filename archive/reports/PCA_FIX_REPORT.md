# PCA Fix Report

Date: 2026-05-04

## What Was Wrong

### 1. The DOCX structure was not detected

The source file `documents/corpus_clean.docx` stores every paragraph as Word style `Normal`. The old extractor only detected headings from Word heading styles like `Heading 1` or markdown markers like `#`.

Result before the fix:

- `338` chunks
- `1` detected section: `Introduction`
- `1` detected chapter: `Introduction générale`
- Real headings like `Matériel & Méthodes`, `Results`, `Discussion`, and `Conclusion` were treated as normal text.

This made the PCA impossible to read by document structure because every point had almost the same metadata.

### 2. Some chunks were just headings

The old chunking process allowed short heading-only chunks.

Examples:

- `Matériel & Méthodes`
- `Results`
- `Conclusion`
- `Limites et développements de la théorie de la niche`

Those chunks are weak for embeddings because they contain little semantic context.

### 3. Repeated section names were merged

The old grouping key used only the section title. If multiple chapters had a section called `Introduction` or `Discussion`, they could be merged together.

### 4. The PCA plot had no useful visual encoding

The old plot used one color for every point:

```python
plt.scatter(..., c='blue')
```

There were no chapter colors, cluster IDs, saved PCA stats, or variance labels.

### 5. PCA itself is limited

PCA compresses 768-dimensional embeddings into 2 dimensions. It is useful as a diagnostic, but it cannot preserve all semantic relationships.

Before the fix, PCA 2D preserved only `18.55%` of the embedding variance.

## What I Fixed

### `backend/process_docx.py`

- Added heuristic heading detection for DOCX files where headings are styled as `Normal`.
- Detects title-like paragraphs using length, punctuation, citation checks, and known section names.
- Detects chapter headings like `Chapitre1`, `Chapitre 4`, and `Introduction générale`.
- Keeps headings as metadata instead of treating the whole document as one section.
- Made graph and Neo4j steps optional so regenerating chunks/PCA does not force the full graph pipeline.
- Added repo-root path setup so `python backend/process_docx.py` runs correctly.

### `backend/chunking.py`

- Skips standalone `heading`, `figure`, and `table` entries during chunk text creation.
- Groups chunks by `(section_index, section)` instead of section title only.
- Reduced chunk size from `1200` to `900` characters for tighter semantic chunks.
- Raised the minimum chunk length to `120` characters to remove heading-only chunks.
- Made the sentence-transformer dependency lazy so simple chunking does not load the embedding model unnecessarily.
- Added fallback chunking if `langchain-text-splitters` is unavailable.

### `backend/vector_store.py`

- Added KMeans cluster IDs to `indexed_chunks.json`.
- Added `plot_label` for each chunk.
- Colors PCA points by chapter when usable chapter metadata exists.
- Shows PCA variance in the chart title and axis labels.
- Saves diagnostic stats to `data/pca_stats.json`.
- Saves a clearer, higher-resolution `data/pca_visualization.png`.

## Regenerated Files

- `data/corpus_cleaned_fr.json`
- `data/corpus_chunks.json`
- `data/faiss_index.bin`
- `data/indexed_chunks.json`
- `data/pca_model.pkl`
- `data/pca_stats.json`
- `data/pca_visualization.png`

## Improvement After The Fix

| Metric | Before | After |
| --- | ---: | ---: |
| Chunks | `338` | `375` |
| Detected sections | `1` | `78` |
| Detected chapters | `1` | `5` |
| Chunks under 120 chars | `15` | `0` |
| Chunks over 1000 chars | `156` | `0` |
| Median chunk length | `966.5` | `899` |
| PCA 2D variance | `18.55%` | `20.12%` |
| PCA colors | none | by chapter |
| PCA stats file | no | yes |
| Cluster IDs in indexed chunks | no | yes |

## How It Improved The PCA

The PCA is now more interpretable because colors represent real chapters instead of one undifferentiated corpus. The plot also shows how much variance PC1 and PC2 preserve, so the user can judge whether PCA is a strong or weak view of the embeddings.

The PCA did not become perfectly separated, and that is expected. The corpus is semantically related throughout, and PCA still preserves only about `20.1%` of the embedding space. The improvement is that the visualization now explains the document structure and exposes useful diagnostics.

## How It Improved The Project

- Retrieval metadata is better because chunks now carry real chapter and section information.
- Future source display can show meaningful section/chapter names.
- Chunk quality is more consistent.
- Heading-only noise was removed from embeddings.
- Pipeline regeneration is easier because graph and Neo4j are optional.
- PCA diagnostics are saved in machine-readable JSON for future debugging.

## Next Best Improvement

For an even clearer semantic map, add an interactive Plotly view or UMAP/t-SNE projection. PCA should remain as a quick diagnostic, but UMAP/t-SNE will usually show semantic neighborhoods more clearly.
