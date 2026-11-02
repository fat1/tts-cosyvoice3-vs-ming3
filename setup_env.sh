#!/bin/bash
# 建 ming-tts 环境 + 下载 Ming-3.0-tts-0.5B 权重
set -x
C=/d/miniconda3
$C/Scripts/conda.exe create -y -n ming-tts -c conda-forge python=3.10 pynini=2.1.6 || $C/Scripts/conda.exe create -y -n ming-tts python=3.10
P=$C/envs/ming-tts/python.exe
export PYTHONNOUSERSITE=1
$P -m pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
$P -m pip install -r /d/steven/models/Ming-3.0-tts/requirements.txt
$P -m pip install openai-whisper
$P -c "from huggingface_hub import snapshot_download; print(snapshot_download('inclusionAI/Ming-3.0-tts-0.5B', local_dir=r'D:\steven\models\Ming-3.0-tts-0.5B'))"
$P -c "import torch, pynini; print('torch', torch.__version__, torch.cuda.is_available(), 'pynini ok')"
echo SETUP_DONE
