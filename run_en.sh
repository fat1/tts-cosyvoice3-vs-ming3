#!/bin/bash
# 整句英文测试：等量化队列停下 → CV3（生产方式）→ Ming（English）→ 打分 → 删 STOP、重启量化队列。
# 用法（后台）: bash tts_compare/run_en.sh >> tts_compare/en/run_en.log 2>&1
cd /d/steven/videos_generated_CC/tts_compare
export PYTHONNOUSERSITE=1 PYTHONIOENCODING=utf-8
Q=/d/steven/videos_generated_CC/studio/series/quant
until tail -1 $Q/run_all.log | grep -q "run_all 结束"; do sleep 60; done
echo "$(date '+%m-%d %T') 队列已停，开始整句英文测试"
/d/miniconda3/envs/tts-gpu/python.exe gen_cv3_en.py || echo "gen_cv3_en 失败 rc=$?"
echo "$(date '+%m-%d %T') cv3 完成"
MING_SET=en MING_LANG=English MING_OUT=en_ming /d/miniconda3/envs/ming-tts/python.exe gen_ming.py || echo "gen_ming 失败 rc=$?"
echo "$(date '+%m-%d %T') ming 完成"
/d/miniconda3/envs/tts-gpu/python.exe score_en.py || echo "score_en 失败 rc=$?"
echo "$(date '+%m-%d %T') 打分完成，重启量化队列"
rm -f $Q/STOP
cd /d/steven/videos_generated_CC
echo "$(date '+%m-%d %T') 整句英文测试结束，重启量化队列" >> $Q/run_all.log
nohup bash studio/series/quant/run_all.sh >> studio/series/quant/run_all.log 2>&1 &
echo "$(date '+%m-%d %T') run_en 结束"
