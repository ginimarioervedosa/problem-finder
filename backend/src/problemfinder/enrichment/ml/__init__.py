"""ML theme proposal: embeddings, clustering, and the cluster review step.

Everything heavyweight (sentence-transformers, scikit-learn, numpy) is
imported lazily inside functions, never at module level: the core install
carries no ml extras and `import problemfinder.enrichment.ml.*` must always
succeed. Missing extras surface as MlExtrasMissingError at call time.
"""
