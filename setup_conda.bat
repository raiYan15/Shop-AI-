@echo off
conda create -n shopmind-ai python=3.10 -y
call conda activate shopmind-ai
pip install -r requirements.txt
echo Conda environment "shopmind-ai" created.
echo To activate: conda activate shopmind-ai
