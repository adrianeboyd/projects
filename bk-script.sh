#!/bin/bash

echo "Set up requirements"
python3.7 -m pip -q install "spacy>=3.2.0,<3.5.0" pytest wheel "numpy<1.20.0" "spacy_lookups_data>=1.0.2,<1.1.0" torch==1.7.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
# for pipelines/floret_wiki_oscar_vectors
python3.7 -m pip -q install floret more-itertools datasets
python3.7 -m pip -q install "wikiextractor @ git+https://github.com/adrianeboyd/wikiextractor.git@v3.0.7a0"

status=0
declare -a project_collections=("benchmarks")  #  "experimental" "integrations" "pipelines" "tutorials"
for project_collection in "${project_collections[@]}"
do
  for project in $project_collection/*/; do
    echo "*** Executing tests for ${project}"
    if [ -e $project/requirements.txt ]; then
      echo "  Installing dependencies"
      python3.7 -m pip -q install -r $project/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
    fi
    python3.7 -m pytest -q -s $project || status=1
    if [ -e $project/requirements.txt ]; then
      echo "  Uninstalling dependencies"
      python3.7 -m pip -q uninstall -y -r $project/requirements.txt
    fi
    echo "  Status: ${status}"
  done
done

exit $status