#!/bin/bash
# 第三方标准参考音重测：两边都不套读音表。Q1 中英混读（REF=zh）、Q2 整句英文（REF=en），每句 3 次。
# 用法（后台）: bash tts_compare/run_std.sh >> tts_compare/run_std.log 2>&1
cd /d/steven/videos_generated_CC/tts_compare
export PYTHONNOUSERSITE=1 PYTHONIOENCODING=utf-8
C=/d/miniconda3/envs
echo "$(date '+%m-%d %T') 开始"
$C/tts-gpu/python.exe prep_ref.py
REF=zh CV3_OUT=std_zh_cv3 $C/tts-gpu/python.exe gen_cv3.py || echo "cv3 zh 失败"
echo "$(date '+%m-%d %T') cv3 zh 完成"
REF=zh MING_LANG=Chinese MING_OUT=std_zh_ming $C/ming-tts/python.exe gen_ming.py || echo "ming zh 失败"
echo "$(date '+%m-%d %T') ming zh 完成"
REF=en CV3_SET=en CV3_OUT=std_en_cv3 $C/tts-gpu/python.exe gen_cv3.py || echo "cv3 en 失败"
echo "$(date '+%m-%d %T') cv3 en 完成"
REF=en MING_SET=en MING_LANG=English MING_OUT=std_en_ming $C/ming-tts/python.exe gen_ming.py || echo "ming en 失败"
echo "$(date '+%m-%d %T') ming en 完成"
REF=zh TAG=std $C/tts-gpu/python.exe score.py || echo "score 失败"
REF=en TAG=std $C/tts-gpu/python.exe score_en.py || echo "score_en 失败"
echo "$(date '+%m-%d %T') run_std 结束"
