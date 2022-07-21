#!/bin/bash

# Make sure Python interpreter is supplied.
if (( $# == 0 )); then
    >&2 echo "Python interpreter (e.g. 'python', 'python3.7') must be supplied."
fi

# Only run tests in second-level directories that have been changed in the last commit.
status=0

# Fetch changed files.
mapfile -t dirs < <( git diff --dirstat=files,0 HEAD~1 | sed 's/^[ 0-9.]\+% //g')
declare -a tested_dirs=()

# For complete run independent from Git changes: bash run-tests.sh all
if [[ $2 == "all" ]]; then
  echo "Executing all tests"
  declare -a project_collections=("benchmarks" "experimental" "integrations" "pipelines" "tutorials")
  declare -a dirs=()
  for dir in "${project_collections[@]}"
  do
    mapfile -d $'\0' second_level_dirs < <(find ${dir} -mindepth 1 -maxdepth 1 -type d -print0)
    for second_level_dir in "${second_level_dirs[@]}"
    do
      dirs+=($second_level_dir)
    done
  done
fi

for dir in "${dirs[@]}"
do
  # Get path with second level only. This will be empty if the change happened at the first level.
  second_level_dir=$(echo "$dir" | awk -F/ '{print FS $2}')
  second_level_dir="${second_level_dir:1}"
  # Get path with first level/second level.
  full_second_level_dir=$(echo "$dir" | cut -d/ -f1-2)

  # Only run if change happened at second level, since first level-changes don't require the tests to be re-run.
  # If change happened at first level, $second_level_dir will be empty.
  if [ ! -z "$second_level_dir" -a "$second_level_dir" != " " ]; then
    if [[ ! " ${tested_dirs[*]} " =~ " ${full_second_level_dir} " ]]; then
      echo "Executing tests for $full_second_level_dir"

      tested_dirs+=($full_second_level_dir)
      if [ -e $full_second_level_dir/requirements.txt ]; then
        $1 -m pip -q install -r $full_second_level_dir/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
      fi

      # Ensure proper spaCy version is installed.
      spacy_version=$(grep -A3 "spacy_version:" ${full_second_level_dir}/project.yml | head -n1 | cut -c 17- | rev | cut -c 2- | rev)
      if [ ! -z "$spacy_version" ]; then
          $1 -m pip -q install spacy${spacy_version}
      fi

      $1 -m pytest -q -s $full_second_level_dir

      # Mark as failure if exit code isn't either 0 (success) or 5 (no tests found).
      if [[ $? != @(0|5) ]]; then
        status=1
      fi

      if [ -e $full_second_level_dir/requirements.txt ]; then
        $1 -m pip freeze --exclude torch --exclude wheel cupy-cuda110 > installed.txt
        $1 -m pip -q uninstall -y -r installed.txt
        $1 -m pip -q install pytest spacy
        rm installed.txt
      fi
    fi
  fi
done

exit $status
