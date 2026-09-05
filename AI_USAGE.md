# AI_USAGE.md

I used AI support during the assignment as a supplementary tool for reasoning, troubleshooting, and reviewing my work. I used it to help clarify the assignment requirements, sanity-check calculations, and discuss possible approaches when I encountered implementation issues.

The analysis, experiments, and final decisions were carried out and verified locally using the provided starter kit, assignment files, corpus data, and my own scripts.

AI assistance was mainly used for:

* understanding and organizing the assignment requirements;
* discussing possible approaches for the multilingual tokenizer audit;
* checking the KV-cache capacity calculations in Part B;
* reviewing intermediate results and helping identify potential inconsistencies;
* helping structure the final findings into the required memo format.

I independently ran and verified the implemented experiments using:

```bash
python partA/fetch_corpus.py
python partA/train_sentencepiece.py
python partA/analyze_tokenizers.py
python partA/audit_checks.py
python partB/capacity_reconciliation.py
```

For the tokenizer work, I initially considered using a Hugging Face `mt5-small` tokenizer. After encountering dependency and cache-resolution issues in the local environment, I changed the approach and used locally trained SentencePiece tokenizers. This made the analysis reproducible without depending on a remote model download during the defense.

The numerical results and conclusions included in the submission were checked against the local script outputs, starter-kit files, and benchmark data. I am responsible for the final implementation, analysis, and decisions in the submission; AI was used as a supporting tool rather than as a replacement for the experimental work.
