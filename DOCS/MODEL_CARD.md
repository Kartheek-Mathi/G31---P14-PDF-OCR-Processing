# Model card: DocWeave relation classifier

## Intended use

A small supervised relation classifier for the fictional WorkflowBench-S ontology. Input is a short English statement with entity identities masked into type tokens. Output is one of eight workflow predicates or `NO_RELATION`. Typed endpoint extraction and a negative/modal guard surround the classifier. This is not a foundation model, LLM, general named-entity recognizer or legal reasoning system.

## Training

The neural model uses a 32-dimensional embedding, a bidirectional LSTM with hidden size 32 per direction, max pooling, a 32-unit ReLU layer and a nine-class output. It has **21,705** parameters. Training used 300 statements, Adam learning rate 0.003, batch size 32, gradient clipping at 1.0 and 100 epochs. Seed 573 controls initialization and shuffling. The earliest highest development macro F1 selects the checkpoint: epoch 5 in the recorded run. Nine development documents (90 statements) were used for selection; test labels were not used. CPU execution used one thread.

The classical comparator is TF-IDF unigram/bigram logistic regression with C=1 and max_iter=1000. Its feature vocabulary and IDF values are fitted on the training set only. Portable JSON/NPZ files avoid loading a scikit-learn pickle. The neural state dict is loaded with `weights_only=True`; only trusted model files should be used.

## Results and limitations

Both learned methods score macro F1 1.000 on the ordinary entity-disjoint test. On the positive-only unseen-phrase slice, logistic regression scores 0.833 and BiLSTM scores 0.708. The neural model is not the strongest measured method on domain-shifted phrasing. Its use as the application's default demonstrates the sequence-model implementation, not a claim of superiority. Launch `python CODE/run.py serve --extractor logistic` to use the classical extractor for new uploads; reseed/reingest to change existing stored relationships.

Normal splits share phrase families, and entity extraction is a handcrafted grammar. The model is uncalibrated. A softmax score must not be interpreted as a validated probability that the graph fact is true. Repeated errors across nine entity substitutions represent two failing neural templates, not eighteen independent linguistic phenomena. One training seed and no real independent dataset were evaluated.

## Data and usage risks

The fictional corpus contains no real people or confidential records. Its narrow distributions do not establish fairness, multilingual support, privacy protection or deployment safety. Negation and modality handling are conservative string guards and can miss complex syntax. Use source evidence to review predictions; quotes prove provenance, not semantic correctness. Do not use this model for consequential legal, employment, financial or medical decisions.
