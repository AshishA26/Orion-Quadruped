import onnxruntime as ort
providers = ort.get_available_providers()

if 'CUDAExecutionProvider' in providers:
    print("Success! GPU acceleration is available.")
else:
    print("Warning: Only CPU (or others) found:", providers)