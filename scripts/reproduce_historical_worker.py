"""Execute unchanged historical code using the explicitly recorded LiteRT runtime."""
import json
from pathlib import Path
import runpy
import sys
import types

from ai_edge_litert.interpreter import Interpreter

# The old script imports tensorflow or tflite_runtime. This compatibility name
# selects the installed LiteRT Interpreter explicitly; no model/metric code changes.
runtime=types.ModuleType('tflite_runtime')
interpreter=types.ModuleType('tflite_runtime.interpreter');interpreter.Interpreter=Interpreter
sys.modules['tensorflow']=None
sys.modules['tflite_runtime']=runtime;sys.modules['tflite_runtime.interpreter']=interpreter
work=Path(sys.argv[1])
namespace=runpy.run_path(str(work/'benchmark_models.py'),run_name='__main__')
predictions={name:results for name,results,*_ in namespace['models']}
(work/'predictions.json').write_text(json.dumps(predictions,default=float)+'\n')
