#!/bin/bash
# CV3 生成 → Ming 生成 → 打分。D 盘空间紧张，跑完不自动重启量化队列（STOP 保留）。
# 用法（后台）: bash tts_compare/run_test.sh >> tts_compare/run_test.log 2>&1
cd /d/steven/videos_generated_CC/tts_compare
export PYTHONNOUSERSITE=1 PYTHONIOENCODING=utf-8
# 权重在别处下载；Ming 之前再等
echo "$(date '+%m-%d %T') 开始测试"
/d/miniconda3/envs/tts-gpu/python.exe gen_cv3.py || echo "gen_cv3 失败 rc=$?"
echo "$(date '+%m-%d %T') cv3 完成"
until [ "$(stat -c %s /d/steven/models/Ming-3.0-tts-0.5B/model.safetensors 2>/dev/null)" = 2959055504 ]; do sleep 30; done
/d/miniconda3/envs/ming-tts/python.exe gen_ming.py || echo "gen_ming 失败 rc=$?"
echo "$(date '+%m-%d %T') ming 完成"
/d/miniconda3/envs/tts-gpu/python.exe score.py || echo "score 失败 rc=$?"
echo "$(date '+%m-%d %T') run_test 结束"
