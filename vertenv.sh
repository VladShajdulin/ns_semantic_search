cd notebooks
jupyter nbconvert --to *.ipynb
pipreqs . --force --mode no-pin --savepath requirements.in --encoding=utf-8
conda activate my-env
pip-compile requirements.in --output-file=requirements.txt --no-annotate